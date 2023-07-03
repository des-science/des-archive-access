import argparse
import os

import requests
from tqdm import tqdm


def main_download():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-download",
        description="download the metadata for the DES archive at FNAL",
    )
    parser.parse_args()

    mloc = os.path.expanduser("~/.des_archive_access/metadata.db")
    if not os.path.exists(mloc):

        os.makedirs(os.path.dirname(mloc), exist_ok=True)

        # https://stackoverflow.com/questions/37573483/progress-bar-while-download-file-over-http-with-requests
        url = (
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
            with open("test.dat", "wb") as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            try:
                os.remove(mloc)
            except Exception:
                pass
            raise RuntimeError("Download failed!")
