import os
import subprocess


def test_download_help():
    res = subprocess.run(
        "des-archive-access-download --help",
        shell=True,
        check=True,
        capture_output=True,
    )
    assert "usage: des-archive-access-download" in res.stdout.decode("utf-8")


def test_download():
    mloc = os.path.expanduser("~/.des_archive_access/metadata.db")
    try:
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
        subprocess.run(
            "des-archive-access-download --remove",
            shell=True,
            check=True,
            capture_output=True,
        )

        assert not os.path.exists(mloc)
