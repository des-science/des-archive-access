import os
import subprocess

from des_archive_access.cli import get_des_archive_access_db


def test_download_help():
    res = subprocess.run(
        "des-archive-access-download --help",
        shell=True,
        check=True,
        capture_output=True,
    )
    assert "usage: des-archive-access-download" in res.stdout.decode("utf-8")


def test_download(tmpdir):
    old_db = get_des_archive_access_db()
    env_var_set = "DES_ARCHIVE_ACCESS_DB" in os.environ

    try:
        os.environ["DES_ARCHIVE_ACCESS_DB"] = os.path.join(
            tmpdir, "dadd", "metadata.db"
        )
        assert get_des_archive_access_db() == os.path.join(
            tmpdir, "dadd", "metadata.db"
        )

        mloc = get_des_archive_access_db()
        res = subprocess.run(
            "des-archive-access-download "
            "--url "
            "https://black.readthedocs.io/en/stable/"
            "usage_and_configuration/the_basics.html",
            shell=True,
            check=True,
            capture_output=True,
        )
        assert "downloading DB" in res.stderr.decode("utf-8")
        assert os.path.exists(mloc)

        res = subprocess.run(
            "des-archive-access-download "
            "--url "
            "https://black.readthedocs.io/en/stable/"
            "usage_and_configuration/the_basics.html",
            shell=True,
            check=True,
            capture_output=True,
        )
        assert res.stderr.decode("utf-8") == ""
        assert res.stdout.decode("utf-8") == ""
        assert os.path.exists(mloc)

        res = subprocess.run(
            "des-archive-access-download "
            "--force "
            "--url "
            "https://black.readthedocs.io/en/stable/"
            "usage_and_configuration/the_basics.html",
            shell=True,
            check=True,
            capture_output=True,
        )
        assert "downloading DB" in res.stderr.decode("utf-8")
        assert os.path.exists(mloc)
    finally:
        if env_var_set:
            os.environ["DES_ARCHIVE_ACCESS_DB"] == old_db
        else:
            del os.environ["DES_ARCHIVE_ACCESS_DB"]
