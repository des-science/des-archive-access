import os
import sqlite3
import subprocess
from functools import lru_cache


def get_des_archive_access_dir():
    """Get the current DES_ARCHIVE_ACCESS_DIR."""
    return os.environ.get(
        "DES_ARCHIVE_ACCESS_DIR",
        os.path.expanduser("~/.des_archive_access"),
    )


def make_des_archive_access_dir():
    """Make the DES_ARCHIVE_ACCESS_DIR and set permissions to 700."""
    daad = get_des_archive_access_dir()
    os.makedirs(daad, exist_ok=True)
    os.chmod(daad, 0o700)


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


def download_file(fname, prefix=None, desdata=None, force=False):
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

    cmd = (
        "curl -k -L --cert "
        "{}:${{DES_ARCHIVE_ACCESS_PASSWORD}} -o {} -C - {}/{}"
    ).format(
        os.path.join(get_des_archive_access_dir(), "cert.p12"),
        fpth,
        prefix,
        fname,
    )
    subprocess.run(cmd, shell=True, check=True, cwd=desdata)
    return fpth
