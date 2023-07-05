import argparse
import contextlib
import os
import subprocess
import sys
import tempfile

import requests
from tqdm import tqdm

from des_archive_access.dbfiles import (
    download_file,
    get_des_archive_access_db,
    get_des_archive_access_dir,
    make_des_archive_access_dir,
)


# https://stackoverflow.com/questions/6194499/pushd-through-os-system
@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


def main_download():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-download",
        description="download files from the DES archive at FNAL",
    )
    parser.add_argument(
        "file",
        type=str,
        default=None,
        help="file to download",
        nargs="?",
    )
    parser.add_argument(
        "-l",
        "--list",
        type=str,
        default=None,
        help="download all files in a list",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        type=str,
        default=None,
        help="HTTPS address of the archive",
    )
    parser.add_argument(
        "-dd",
        "--desdata",
        type=str,
        default=None,
        help="The destination DESDATA directory.",
    )
    args = parser.parse_args()

    prefix = args.prefix or os.environ.get(
        "DES_ARCHIVE_ACCESS_PREFIX",
        "https://fndcadoor.fnal.gov:2880/des/persistent/DESDM_ARCHIVE",
    )

    desdata = args.desdata or os.environ["DESDATA"]

    if args.file is not None:
        print(download_file(args.file, prefix=prefix, desdata=desdata))

    if args.list is not None:
        with open(args.list) as fp:
            for line in fp:
                line = line.strip()
                download_file(line, prefix=prefix, desdata=desdata)


def main_download_metadata():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-download-metadata",
        description="download the metadata for the DES archive at FNAL",
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

        try:
            # https://stackoverflow.com/questions/37573483/progress-bar-while-download-file-over-http-with-requests
            url = args.url or (
                "http://deslogin.cosmology.illinois.edu/~donaldp/"
                "desdm-file-db-23-05-03-13-33/desdm-test.db"
            )
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
                with open(mloc, "wb") as file:
                    for data in response.iter_content(block_size):
                        progress_bar.update(len(data))
                        file.write(data)
            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                raise RuntimeError("Download failed!")
        except (KeyboardInterrupt, Exception) as e:
            try:
                os.remove(mloc)
            except Exception:
                pass

            raise e


def _check_openssl_version():
    res = subprocess.run(
        "openssl version",
        shell=True,
        check=True,
        capture_output=True,
    )
    version = res.stdout.decode("utf-8").split()[1]
    assert version[0] == "3", (
        "OpenSSL version needs to be at least version 3: found %s" % version
    )
    return version


def main_process_cert():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-process-cert",
        description="process the CILogon certificate for DES archive access",
    )
    parser.add_argument(
        "cert",
        type=str,
        help="certificate to process",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="forcibly replace the current certificate",
    )
    parser.add_argument(
        "--remove", action="store_true", help="remove existing certificate"
    )
    args = parser.parse_args()

    cloc = os.path.join(get_des_archive_access_dir(), "cert.p12")

    if args.remove or args.force:
        try:
            os.remove(cloc)
        except Exception:
            pass

    if args.remove:
        sys.exit(0)

    if args.cert is not None and (not os.path.exists(cloc) or args.force):
        _check_openssl_version()
        make_des_archive_access_dir()

        try:
            with tempfile.TemporaryDirectory() as tmpdir, pushd(tmpdir):
                subprocess.run(
                    "openssl pkcs12 -in %s -nodes -legacy > temp" % args.cert,
                    shell=True,
                    check=True,
                )
                subprocess.run(
                    "openssl pkcs12 -export -out %s -in temp" % cloc,
                    shell=True,
                    check=True,
                )
        except (KeyboardInterrupt, Exception) as e:
            try:
                os.remove(cloc)
            except Exception:
                pass

            raise e
