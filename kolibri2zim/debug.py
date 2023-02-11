import io
import logging
import pathlib
import re
import tempfile
import urllib.parse
from typing import Optional, Union

import libzim.writer
import requests
from zimscraperlib.download import stream_file, _get_retry_adapter
from zimscraperlib.zim.items import StaticItem

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("DEBUG")
# size[464505] == provider->getSize()[1226905]
# 453.62 KiB      1.17 MiB

bs1 = 464505
bs2 = 1226905
bss = [bs1, bs2]

session = requests.Session()
session.mount("http", _get_retry_adapter())


class URLProvider(libzim.writer.ContentProvider):
    """Provider downloading content as it is consumed by the libzim

    Useful for non-indexed content for which feed() is called only once"""

    def __init__(
        self, url: str, size: Optional[int] = None, ref: Optional[object] = None
    ):
        super().__init__()
        self.url = url
        self.size = size if size is not None else self.get_size_of(url)
        self.ref = ref

        self.resp = session.get(url, stream=True)
        self.resp.raise_for_status()

    @staticmethod
    def get_size_of(url) -> Union[int, None]:
        _, headers = stream_file(url, byte_stream=io.BytesIO(), only_first_block=True)
        try:
            return int(headers["Content-Length"])
        except Exception:
            return None

    def get_size(self) -> int:
        return self.size

    def gen_blob(self) -> libzim.writer.Blob:  # pragma: nocover
        for chunk in self.resp.iter_content(10 * 1024):
            if chunk:
                yield libzim.writer.Blob(chunk)
        yield libzim.writer.Blob(b"")


class URLItem(StaticItem):
    """StaticItem to automatically fetch and feed an URL resource

    Appropriate for retrieving/bundling static assets that you don't need to
    post-process.

    Uses URL's path as zim path if none provided
    Keeps single in-memory copy of content for HTML resources (indexed)
    Works transparently on servers returning a Content-Length header (most)
    *Swaps* a copy of the content either in memory or on disk (`use_disk=True`)
    in case the content size could not be retrieved from headers.
    Use `tmp_dir` to point location of that temp file."""

    @staticmethod
    def download_for_size(url, on_disk, tmp_dir=None):
        """Download URL to a temp file and return its tempfile and size"""
        fpath = stream = None
        if on_disk:
            suffix = pathlib.Path(re.sub(r"^/", "", url.path)).suffix
            fpath = pathlib.Path(
                tempfile.NamedTemporaryFile(
                    suffix=suffix, delete=False, dir=tmp_dir
                ).name
            )
        else:
            stream = io.BytesIO()
        size, _ = stream_file(url.geturl(), fpath=fpath, byte_stream=stream)
        return fpath or stream, size

    def __init__(self, url: str, **kwargs):
        super().__init__(**kwargs)
        self.url = urllib.parse.urlparse(url)
        use_disk = getattr(self, "use_disk", False)
        nostream_threshold = getattr(self, "nostream_threshold", -1)

        logger.info(f"> {self.url.geturl()}")

        # fetch headers to retrieve size and type
        try:
            _, self.headers = stream_file(
                url, byte_stream=io.BytesIO(), only_first_block=True
            )
        except Exception as exc:
            raise IOError(f"Unable to access URL at {url}: {exc}")

        # HTML content will be indexed.
        # we proxy the content in the Item to prevent double-download of the resource
        # we use a value-variable to prevent race-conditions in the multiple
        # reads of the content in the provider
        if self.should_index:
            self.fileobj = io.BytesIO()
            self.size, _ = stream_file(self.url.geturl(), byte_stream=self.fileobj)
            logger.info(f"> {self.url.geturl()} SHOULD_INDEX {self.size=}")
            if self.size in bss:
                logger.error("FOUND {self.url.geturl()} HAS {self.size}")
            return

        try:
            # Encoded data (compressed) prevents us from using Content-Length header
            # as source for the content (it represents length of compressed data)
            if self.headers.get("Content-Encoding", "identity") != "identity":
                raise ValueError("Can't trust Content-Length for size")
            # non-html, non-compressed data.
            self.size = int(self.headers["Content-Length"])
            logger.info(f"> {self.url.geturl()} Content-Length {self.size=}")
            if self.size in bss:
                logger.error("FOUND {self.url.geturl()} HAS {self.size}")
        except Exception:
            # we couldn't retrieve size so we have to download resource to
            target, self.size = self.download_for_size(
                self.url, on_disk=use_disk, tmp_dir=getattr(self, "tmp_dir", None)
            )
            logger.info(f"> {self.url.geturl()} Downloaded {self.size=}")
            if self.size in bss:
                logger.error("FOUND {self.url.geturl()} HAS {self.size}")
            # downloaded to disk and using a file path from now on
            if use_disk:
                self.filepath = target
            # downloaded to RAM and using a bytes object
            else:
                self.fileobj = target

        if self.size and nostream_threshold and self.size <= nostream_threshold:
            self.fileobj = io.BytesIO()
            stream_file(self.url.geturl(), byte_stream=self.fileobj)

    def get_path(self) -> str:
        return getattr(self, "path", re.sub(r"^/", "", self.url.path))

    def get_title(self) -> str:
        return getattr(self, "title", "")

    def get_mimetype(self) -> str:
        return getattr(
            self,
            "mimetype",
            self.headers.get("Content-Type", "application/octet-stream"),
        )

    def get_contentprovider(self):
        try:
            return super().get_contentprovider()
        except NotImplementedError:
            if not getattr(self, "size", None):
                logger.info("> {self.url.geturl()} HAS NO SIZE FOR CP")
            return URLProvider(
                url=self.url.geturl(), size=getattr(self, "size", None), ref=self
            )
