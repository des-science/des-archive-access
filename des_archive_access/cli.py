import argparse
import os
import sys

import requests
from tqdm import tqdm


def main_download():
    parser = argparse.ArgumentParser(
        prog="des-archive-access-download",
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

    mloc = os.path.expanduser("~/.des_archive_access/metadata.db")

    if args.remove or args.force:
        try:
            os.remove(mloc)
        except Exception:
            pass

    if args.remove:
        sys.exit(0)

    if not os.path.exists(mloc) or args.force:
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
        except Exception as e:
            try:
                os.remove(mloc)
            except Exception:
                pass

            raise e
