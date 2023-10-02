import io
import logging
import pathlib

import requests
from retrying import retry
from zimscraperlib.download import _get_retry_adapter, stream_file
from zimscraperlib.video.encoding import reencode

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("DEBUG")

session = requests.Session()
session.mount("http", _get_retry_adapter())

ON_DISK_THRESHOLD = 2**20 * 20  # 20MiB


# retry up to 3 times, with delay from 40s
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=20000)
def get_size_and_mime(url: str) -> tuple[int | None, str]:
    logger.debug(f"get_size_and_mime({url=})")
    _, headers = stream_file(
        url, byte_stream=io.BytesIO(), only_first_block=True
    )  # type: ignore # see https://github.com/openzim/python-scraperlib/issues/104
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
    fpath: pathlib.Path | None = None,
    byte_stream: io.BytesIO | None = None,
):
    logger.debug(f"download_to({url=}) {'to-file' if fpath else 'to-mem'}")
    stream_file(url, fpath=fpath, byte_stream=byte_stream)


# retry up to three times on subprocess.CalledProcessError
@retry(stop_max_attempt_number=3)
def safer_reencode(*args, **kwargs):
    return reencode(*args, **kwargs)
