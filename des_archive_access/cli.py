import argparse
import os
import subprocess
import sys

import requests
import zstandard
from tqdm import tqdm

from des_archive_access.dbfiles import (
    download_file,
    get_des_archive_access_db,
    get_des_archive_access_dir,
    make_des_archive_access_dir,
)


def main_download():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-download",
        description="Download files from the DES archive at FNAL.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "file",
        type=str,
        default=None,
        help="file to download",
        nargs="?",
    )
    group.add_argument(
        "-l",
        "--list",
        type=str,
        default=None,
        help="download all files in a list",
    )
    parser.add_argument(
        "-a",
        "--archive",
        type=str,
        default=None,
        help="HTTPS address of the FNAL archive",
    )
    parser.add_argument(
        "-d",
        "--desdata",
        type=str,
        default=None,
        help="The destination DESDATA directory.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force the download even if data already exists",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print the 'curl' command and stderr to help debug "
        "connection and download issues.",
    )
    parser.add_argument(
        "--no-refresh-token",
        action="store_true",
        help="Do not attempt to automatically refresh the OIDC token.",
    )
    args = parser.parse_args()

    prefix = args.archive or os.environ.get(
        "DES_ARCHIVE_ACCESS_ARCHIVE",
        "https://fndcadoor.fnal.gov:2880/des/persistent/DESDM_ARCHIVE",
    )

    desdata = args.desdata or os.environ["DESDATA"]

    if args.file is not None:
        print(
            download_file(
                args.file,
                prefix=prefix,
                desdata=desdata,
                force=args.force,
                debug=args.debug,
                refresh_token=not args.no_refresh_token,
            )
        )

    if args.list is not None:
        with open(args.list) as fp:
            # for a list of files we refresh once
            did_refresh = False
            for line in fp:
                line = line.strip()
                download_file(
                    line,
                    prefix=prefix,
                    desdata=desdata,
                    force=args.force,
                    debug=args.debug,
                    refresh_token=((not args.no_refresh_token) and (not did_refresh)),
                )
                did_refresh = True


def main_download_metadata():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-download-metadata",
        description="Download the metadata for the DES archive at FNAL.",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="specify URL to metadata to override default",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="force the download even if metadata already exists",
    )
    parser.add_argument(
        "--remove", action="store_true", help="remove existing metadata"
    )
    args = parser.parse_args()

    mloc = get_des_archive_access_db()

    if args.remove or args.force:
        try:
            os.remove(mloc)
        except Exception:
            pass

    if args.remove:
        sys.exit(0)

    if not os.path.exists(mloc) or args.force:
        if os.path.dirname(mloc) == os.path.expanduser("~/.des_archive_access"):
            make_des_archive_access_dir()
        else:
            os.makedirs(os.path.dirname(mloc), exist_ok=True)

        url = args.url or (
            "http://deslogin.cosmology.illinois.edu/~donaldp/"
            "desdm-file-db-23-10-06-15-39/desdm_pruned_indexed_files.db.zst"
        )

        if url.endswith(".zstd"):
            dest = mloc + ".zstd"
        else:
            dest = mloc

        try:
            if url.startswith("http"):
                # https://stackoverflow.com/questions/37573483/progress-bar-while-download-file-over-http-with-requests
                response = requests.get(url, stream=True)
                total_size_in_bytes = int(response.headers.get("content-length", 0))
                block_size = 1024
                with tqdm(
                    total=total_size_in_bytes,
                    unit="iB",
                    unit_scale=True,
                    ncols=80,
                    desc="downloading DB",
                ) as progress_bar:
                    with open(dest, "wb") as file:
                        for data in response.iter_content(block_size):
                            progress_bar.update(len(data))
                            file.write(data)
                if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                    raise RuntimeError("Download failed!")

                _source_path = mloc + ".zstd"
            else:
                _source_path = url[len("file://") :]

            # decompress
            if url.endswith(".zstd"):
                print("decompressing...", end="", flush=True)
                dctx = zstandard.ZstdDecompressor()
                with open(_source_path, "rb") as ifh, open(mloc, "wb") as ofh:
                    dctx.copy_stream(ifh, ofh)
                print("done.", flush=True)
        except (KeyboardInterrupt, Exception) as e:
            try:
                os.remove(mloc)
                if url.endswith(".zstd"):
                    os.remove(mloc + ".zstd")
            except Exception:
                pass

            raise e
        finally:
            try:
                if url.startswith("http") and url.endswith(".zstd"):
                    os.remove(mloc + ".zstd")
            except Exception:
                pass


def main_make_token():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-make-token",
        description="Make the OIDC token for FNAL dCache. "
        "Any extra arguemnts are passed to `htgettoken`.",
    )
    parser.add_argument("--remove", action="store_true", help="remove existing tokens")
    args, unknown = parser.parse_known_args()
    make_des_archive_access_dir(fix_permissions=True)

    if args.remove:
        for pth in [
            os.path.join(get_des_archive_access_dir(), "vault_token"),
            os.path.join(get_des_archive_access_dir(), "bearer_token"),
        ]:
            try:
                os.remove(pth)
            except Exception:
                pass

    if args.remove:
        sys.exit(0)

    # we use a non-standard default location for the vault token
    # if it does not stomp on user settings
    if not any("--vaulttokenfile" in uk for uk in unknown):
        unknown += [
            "--vaulttokenfile="
            + os.path.join(get_des_archive_access_dir(), "vault_token")
        ]
    extra_args = " ".join(unknown)

    # the output token location and name of vault etc. is always set
    tloc = os.path.join(get_des_archive_access_dir(), "bearer_token")
    cmd = f"htgettoken {extra_args} -a htvaultprod.fnal.gov -i des -o {tloc}"

    # if the user wants verbose or debugging, we print the command
    if (
        (
            "-v" in unknown
            or "-d" in unknown
            or "--debug" in unknown
            or "--verbose" in unknown
        )
        and "-q" not in unknown
        and "--quiet" not in unknown
    ):
        print("RUNNING COMMAND:", cmd, file=sys.stderr)

    subprocess.run(
        cmd,
        shell=True,
        check=True,
    )
