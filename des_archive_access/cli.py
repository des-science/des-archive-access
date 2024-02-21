import argparse
import os
import subprocess
import sys
import tempfile

import requests
import zstandard
from tqdm import tqdm

from des_archive_access.dbfiles import (
    download_file,
    download_file_from_desdm,
    get_des_archive_access_db,
    get_des_archive_access_dir,
    make_des_archive_access_dir,
)


def main_download():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-download",
        description=(
            "Download files from the DES archive at FNAL. "
            "Any extra keyword arguemnts are passed to `curl`."
        ),
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
    args, unknown = parser.parse_known_args()

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
                extra_cli_args=" ".join(unknown),
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
                    extra_cli_args=" ".join(unknown),
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

        if url.endswith(".zst"):
            dest = mloc + ".zst"
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

                _source_path = dest
            else:
                _source_path = url[len("file://") :]

            # decompress
            if url.endswith(".zst"):
                print("decompressing...", end="", flush=True)
                dctx = zstandard.ZstdDecompressor()
                with open(_source_path, "rb") as ifh, open(mloc, "wb") as ofh:
                    dctx.copy_stream(ifh, ofh)
                print("done.", flush=True)
        except (KeyboardInterrupt, Exception) as e:
            try:
                os.remove(mloc)
                if url.endswith(".zst"):
                    os.remove(mloc + ".zst")
            except Exception:
                pass

            raise e
        finally:
            try:
                if url.startswith("http") and url.endswith(".zst"):
                    os.remove(mloc + ".zst")
            except Exception:
                pass


def main_make_token():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-make-token",
        description="Make the OIDC token for FNAL dCache. "
        "Any extra arguemnts are passed to `htgettoken`.",
    )
    parser.add_argument("--remove", action="store_true", help="remove existing tokens")
    parser.add_argument("--force", action="store_true", help="forcibly remake tokens")
    args, unknown = parser.parse_known_args()
    make_des_archive_access_dir(fix_permissions=True)

    if args.remove or args.force:
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

    for pth in [
        os.path.join(get_des_archive_access_dir(), "vault_token"),
        os.path.join(get_des_archive_access_dir(), "bearer_token"),
    ]:
        os.chmod(pth, 0o700)


PIZZA_CUTTER_CONFIG = """\
des_data:
  campaign: Y6A2_COADD
  source_type: finalcut
  piff_campaign: Y6A2_PIFF_V3

# optional but these are good defaults
fpack_pars:
  # if you do not set FZTILE, the code sets it to the size of a slice for you
  FZQVALUE: 16
  FZALGOR: "RICE_1"
  # preserve zeros, don't dither them
  FZQMETHD: "SUBTRACTIVE_DITHER_2"
  # do dithering via a checksum
  FZDTHRSD: "CHECKSUM"

coadd:
  # these are in pixels
  # the total "pizza slice" will be central_size + 2 * buffer_size
  central_size: 100  # size of the central region
  buffer_size: 50  # size of the buffer on each size

  # this should be odd and bigger than any stamp returned by the
  # PSF reconstruction
  psf_box_size: 51

  wcs_type: image
  coadding_weight: 'noise'

single_epoch:
  # pixel spacing for building various WCS interpolants
  se_wcs_interp_delta: 8
  coadd_wcs_interp_delta: 100

  # fractional amount to increase coadd box size when getting SE region for
  # coadding - set to sqrt(2) for full position angle rotations
  frac_buffer: 1

  # set this to either piff or psfex
  # if using piff in DES and a release earlier than Y6,
  # you need to set the piff_run above too
  psf_type: piff
  psf_kwargs:
    g:
      GI_COLOR: 1.1
    r:
      GI_COLOR: 1.1
    i:
      GI_COLOR: 1.1
    z:
      IZ_COLOR: 0.34
  piff_cuts:
    max_fwhm_cen: 3.6
    min_nstar: 30
    max_exp_T_mean_fac: null
    max_ccd_T_std_fac: null
  mask_piff_failure:
    grid_size: 128
    max_abs_T_diff: 0.15

  # which SE WCS to use - one of piff, pixmappy or image
  wcs_type: pixmappy
  wcs_color: 1.1

  ignored_ccds:
    - 31

  reject_outliers: False
  symmetrize_masking: True
  copy_masked_edges: True
  max_masked_fraction: 0.1
  edge_buffer: 48

  # Y6 already deals with tapebump in a sensible way
  mask_tape_bumps: False

  # DES Y6 bit mask flags
  # "BPM":          1,  #/* set in bpm (hot/dead pixel/column)        */
  # "SATURATE":     2,  #/* saturated pixel                           */
  # "INTERP":       4,  #/* interpolated pixel                        */
  # "BADAMP":       8,  #/* Data from non-functional amplifier        */
  # "CRAY":        16,  #/* cosmic ray pixel                          */
  # "STAR":        32,  #/* bright star pixel                         */
  # "TRAIL":       64,  #/* bleed trail pixel                         */
  # "EDGEBLEED":  128,  #/* edge bleed pixel                          */
  # "SSXTALK":    256,  #/* pixel potentially effected by xtalk from  */
  #                     #/*       a super-saturated source            */
  # "EDGE":       512,  #/* pixel flag to exclude CCD glowing edges   */
  # "STREAK":    1024,  #/* pixel associated with streak from a       */
  #                     #/*       satellite, meteor, ufo...           */
  # "SUSPECT":   2048,  #/* nominally useful pixel but not perfect    */
  # "FIXED":     4096,  # bad coilumn that DESDM reliably fixes       */
  # "NEAREDGE":  8192,  #/* marks 25 bad columns neat the edge        */
  # "TAPEBUMP": 16384,  #/* tape bumps                                */

  spline_interp_flags:
    - 1     # BPM
    - 2     # SATURATE
    - 4     # INTERP. Already interpolated; is this ever set?
    - 16    # CRAY
    - 64    # TRAIL
    - 128   # EDGEBLEED
    - 256   # SSXTALK
    - 512   # EDGE
    - 1024  # STREAK

  noise_interp_flags:
    - 0

  # make the judgment call that it is better to use the somewhat
  # suspect TAPEBUMP/SUSPECT areas than interp, because they are
  # fairly large
  # star areas are ignored for now - GAIA masks will handle them or star-gal sep
  #  - 32    # STAR
  #  - 2048  # SUSPECT
  #  - 4096  # FIXED by DESDM reliably
  #  - 8192  # NEAREDGE 25 bad columns on each edge, removed anyways due to 48 pixel
  #          # boundry
  #  - 16384 # TAPEBUMP

  bad_image_flags:
    # data from non-functional amplifiers is ignored
    - 8     # BADAMP

  gaia_star_masks:
    poly_coeffs: [1.36055007e-03, -1.55098040e-01,  3.46641671e+00]
    max_g_mag: 18.0
    symmetrize: False
    # interp:
    #   fill_isolated_with_noise: False
    #   iso_buff: 1
    apodize:
      ap_rad: 1
    mask_expand_rad: 16
"""


def main_sync_tile_data():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-sync-tile-data",
        description="Sync all data for a given coadd tile from NCSA to FNAL.",
    )
    parser.add_argument(
        "--tilename",
        required=True,
        help="tile to process",
    )
    parser.add_argument(
        "--band",
        help="band to process",
        required=True,
    )
    parser.add_argument(
        "-d",
        "--desdata",
        type=str,
        default=None,
        help="The destination DESDATA directory.",
    )
    args, unknown = parser.parse_known_args()

    dest_desdata = args.desdata or os.environ["DESDATA"]
    if dest_desdata is None:
        dest_desdata = os.path.join(os.path.expanduser("~"), "DESDATA")
    if not os.path.exists(dest_desdata):
        os.makedirs(dest_desdata, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        # make the config file
        config_path = os.path.join(tmpdir, "pizza_cutter_config.yaml")
        with open(config_path, "w") as config_file:
            config_file.write(PIZZA_CUTTER_CONFIG)

        meds_dir = os.path.join(tmpdir, "MEDS_DIR")

        lnk_dir = os.path.join(
            meds_dir,
            "pizza_cutter_config",
            args.tilename,
            f"sources-{args.band}",
        )

        os.makedirs(os.path.dirname(lnk_dir), exist_ok=True)
        os.symlink(dest_desdata, lnk_dir, target_is_directory=True)

        # make the command
        old_meds_dir = os.environ.get("MEDS_DIR", None)
        meds_dir_defined = "MEDS_DIR" in os.environ
        try:
            os.environ["MEDS_DIR"] = meds_dir
            cmd = (
                "des-pizza-cutter-prep-tile "
                f"--config {config_path} "
                f"--tilename {args.tilename} "
                f"--band {args.band} "
            )
            subprocess.run(cmd, shell=True, check=True)
        finally:
            if meds_dir_defined:
                os.environ["MEDS_DIR"] = old_meds_dir
            else:
                del os.environ["MEDS_DIR"]

    tags_to_query = [
        ("Y6A2_BFD_V3", True),
        ("Y6A2_SOF", False),
        ("Y6A2_PIZZACUTTER_V3", True),
        ("Y6A2_MEDS_V3", True),
    ]
    import easyaccess as ea

    try:
        conn = ea.connect(section="desoper")
        curs = conn.cursor()
        for tag, per_band in tags_to_query:
            sql = f"""\
select
    fai.path as path,
    fai.filename as filename,
    fai.compression as compression
from
    proctag t,
    miscfile m,
    file_archive_info fai
where
    t.tag = '{tag}'
    and t.pfw_attempt_id = m.pfw_attempt_id
    and m.tilename = '{args.tilename}'
    and fai.filename = m.filename
    and fai.archive_name = 'desar2home'
"""
            if per_band:
                sql += f"    and m.band = '{args.band}'\n"
            curs.execute(sql)
            rows = curs.fetchall()
            for row in rows:
                archive_path = os.path.join(row[0], row[1])
                if row[2] is not None:
                    archive_path += row[2]
                print(f"downloading {archive_path}", flush=True)
                download_file_from_desdm(archive_path, dest_desdata)
    finally:
        conn.close()
