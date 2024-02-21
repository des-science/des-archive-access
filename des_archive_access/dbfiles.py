import os
import sqlite3
import subprocess
import sys
from functools import lru_cache


def get_des_archive_access_dir():
    """Get the current DES_ARCHIVE_ACCESS_DIR."""
    return os.environ.get(
        "DES_ARCHIVE_ACCESS_DIR",
        os.path.expanduser("~/.des_archive_access"),
    )


def make_des_archive_access_dir(fix_permissions=False):
    """Make the DES_ARCHIVE_ACCESS_DIR and set permissions to 700."""
    daad = get_des_archive_access_dir()
    os.makedirs(daad, exist_ok=True)
    os.chmod(daad, 0o700)
    if fix_permissions:
        for fname in os.listdir(daad):
            os.chmod(os.path.join(daad, fname), 0o600)


def get_des_archive_access_db():
    """Get the metadata DB location."""
    return os.environ.get(
        "DES_ARCHIVE_ACCESS_DB",
        os.path.join(
            os.path.expanduser("~/.des_archive_access"),
            "metadata.db",
        ),
    )


@lru_cache(maxsize=1)
def get_des_archive_access_db_conn():
    """Get a DB connection."""
    dbloc = get_des_archive_access_db()
    return sqlite3.connect(
        f"file:{dbloc}?mode=ro",
        uri=True,
    )


def download_file(
    fname,
    prefix=None,
    desdata=None,
    force=False,
    debug=False,
    refresh_token=True,
    extra_cli_args="",
):
    """Download a file FNAME from the DES FNAL archive
    possibly with an optional HTTPS `prefix` and optional `desdata` destination.

    Returns the local path to the file.
    """
    prefix = prefix or os.environ.get(
        "DES_ARCHIVE_ACCESS_ARCHIVE",
        "https://fndcadoor.fnal.gov:2880/des/persistent/DESDM_ARCHIVE",
    )
    desdata = desdata or os.environ["DESDATA"]

    fpth = os.path.join(desdata, fname)
    os.makedirs(os.path.dirname(fpth), exist_ok=True)
    if force:
        try:
            os.remove(fpth)
        except Exception:
            pass

    if refresh_token:
        try:
            cmd = "des-archive-access-make-token -v"
            r = subprocess.run(
                cmd,
                shell=True,
                check=True,
                text=True,
                # when debugging, we let all stdout/stderr through
                # but put everything in stderr
                # otherwise, we capture it all
                stdout=sys.stderr if debug else subprocess.PIPE,
                stderr=None if debug else subprocess.STDOUT,
            )
        except Exception:
            # if we encounter an error, we print the captured
            # output to stderr and raise a helpful message
            print(r.stdout, file=sys.stderr)
            raise RuntimeError(
                "OIDC token refresh failed!"
                "Run 'des-archive-access-make-token -d' "
                "at the command line to debug."
            )

    cmd = (
        'curl --write-out "%{{http_code}}" -L {} '
        '-H "Authorization: Bearer $(<{})" -o {} -C - {}/{}'
    ).format(
        extra_cli_args,
        os.path.join(get_des_archive_access_dir(), "bearer_token"),
        fpth,
        prefix,
        fname,
    )

    if debug:
        print("RUNNING COMMAND:", cmd, file=sys.stderr)

    res = subprocess.run(
        cmd,
        shell=True,
        check=True,
        cwd=desdata,
        # we always capture stdout since the only thing that should be
        # on stdout is the file path after the download
        stdout=subprocess.PIPE,
        # if we are debugging, we let stderr through
        stderr=None if debug else subprocess.PIPE,
        text=True,
    )

    http_code = int(res.stdout)
    if debug:
        print(f"HTTP return code: {res.stdout}", file=sys.stderr)

    if http_code >= 400:
        if res.stderr:
            print(res.stderr, file=sys.stderr)
        err_str = (
            f"Failed to download file with HTTP error code {http_code}! "
            "Trying the same command on with `--debug` may help you diagnose the error."
        )
        if http_code == 401:
            err_str += (
                " Error code 401 indicates that need to refresh your token "
                "by running 'des-archive-access-make-token' at the command line."
            )
        raise RuntimeError(err_str)

    return fpth


def download_file_from_desdm(archive_path, source_dir):
    """Given a path in the DESDM file archive and the destination directory,
    download the file via rsync.

    Parameters
    ----------
    archive_path : str
        The file to download from the DESDM file archive (e.g.,
        "OPS/cal/cat_tile_gaia/v1/DES0146-3623_GAIA_DR2_v1.fits").
    source_dir : str
        The location to download the file to. The file will be at
        `source_dir`/`archive_path`.
    """

    if "DESREMOTE_RSYNC_USER" in os.environ:
        user = os.environ["DESREMOTE_RSYNC_USER"] + "@"
    else:
        user = ""

    final_dir = os.path.dirname(os.path.join(source_dir, archive_path))
    os.makedirs(final_dir, exist_ok=True)

    rsync_cmd = """\
rsync \
    -av \
    --password-file ${DES_RSYNC_PASSFILE} \
    %(user)s${DESREMOTE_RSYNC}/%(fname)s \
    %(source_dir)s/%(fname)s
""" % dict(
        user=user,
        fname=archive_path,
        source_dir=source_dir,
    )

    subprocess.run(
        rsync_cmd,
        shell=True,
        check=True,
    )
