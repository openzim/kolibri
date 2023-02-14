import io
import logging
import pathlib
from typing import Optional, Tuple

import requests
from retrying import retry
from zimscraperlib.download import stream_file, _get_retry_adapter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("DEBUG")

session = requests.Session()
session.mount("http", _get_retry_adapter())

ON_DISK_THRESHOLD = 2**20 * 20  # 20MiB


# retry up to 3 times, with delay from 40s
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=20000)
def get_size_and_mime(url: str) -> Tuple[int, str]:
    logger.debug(f"get_size_and_mime({url=})")
    _, headers = stream_file(url, byte_stream=io.BytesIO(), only_first_block=True)
    mimetype = headers.get("Content-Type", "application/octet-stream")
    # Encoded data (compressed) prevents us from using Content-Length header
    # as source for the content (it represents length of compressed data)
    if headers.get("Content-Encoding", "identity") != "identity":
        logger.warning(f"Can't trust Content-Length for size ({url=})")
        return None, mimetype
    # non-html, non-compressed data.
    try:
        return int(headers["Content-Length"]), mimetype
    except Exception:
        ...

    return None, mimetype  # couldn't retrieve size


# retry up to 5 times, with delay from 40s to 10mn
@retry(stop_max_attempt_number=5, wait_exponential_multiplier=20000)
def download_to(
    url: str,
    fpath: Optional[pathlib.Path] = None,
    byte_stream: Optional[io.IOBase] = None,
):
    logger.debug(f"download_to({url=}) {'to-file' if fpath else 'to-mem'}")
    stream_file(url, fpath=fpath, byte_stream=byte_stream)
