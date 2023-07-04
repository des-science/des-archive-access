import os
import subprocess

from des_archive_access.cli import get_des_archive_access_dir


def test_download_help():
    res = subprocess.run(
        "des-archive-access-download --help",
        shell=True,
        check=True,
        capture_output=True,
    )
    assert "usage: des-archive-access-download" in res.stdout.decode("utf-8")


def test_download(tmpdir):
    old_daad = get_des_archive_access_dir()
    env_var_set = "DES_ARCHIVE_ACCESS_DIR" in os.environ

    try:
        os.environ["DES_ARCHIVE_ACCESS_DIR"] = os.path.join(tmpdir, "daad")
        assert get_des_archive_access_dir() == os.path.join(tmpdir, "daad")

        mloc = os.path.join(get_des_archive_access_dir(), "metadata.db")
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
            os.environ["DES_ARCHIVE_ACCESS_DIR"] == old_daad
        else:
            del os.environ["DES_ARCHIVE_ACCESS_DIR"]
