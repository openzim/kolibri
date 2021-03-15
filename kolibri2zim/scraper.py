#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import io
import queue
import base64
import zipfile
import pathlib
import datetime
import tempfile
import threading

import jinja2
from zimscraperlib.download import stream_file
from zimscraperlib.zim.creator import Creator
from zimscraperlib.zim.items import URLItem

from .constants import ROOT_DIR, getLogger, STUDIO_URL
from .database import KolibriDB

logger = getLogger()
options = [
    "debug",
    "name",
    "video_format",
    "low_quality",
    "output_dir",
    "fname",
    "title",
    "description",
    "creator",
    "publisher",
    "tags",
    "keep_build_dir",
    "concurrency",
    "autoplay",
    "channel_id",
    "tmp_dir",
]


def get_kolibri_url_for(file_id: str, ext: str):
    """ download URL and filename for a file ID and extension """
    fname = f"{file_id}.{ext}"
    remote_dirs = (file_id[0], file_id[1])
    remote_path = f"{'/'.join(remote_dirs)}/{fname}"
    return f"{STUDIO_URL}/content/storage/{remote_path}", fname


def worker_wrapper(func, chain, *args):
    """ wraps a worker-func for a task queue """
    while True:
        try:
            param = chain.get()
        except queue.Empty:
            return
        try:
            func(param, *args)
        except Exception as exc:
            logger.error(f"Error in worker: {exc}")
            logger.exception(exc)
        finally:
            chain.task_done()


class Kolibri2Zim:
    def __init__(self, **kwargs):

        for option in options:
            if option not in kwargs:
                raise ValueError(f"Missing parameter `{option}`")

        def go(option):
            return kwargs.get(option)

        self.channel_id = go("channel_id")

        # video-encoding info
        self.video_format = go("video_format")
        self.low_quality = go("low_quality")

        # zim params
        self.fname = go("fname")
        self.tags = (
            [] if go("tags") is None else [t.strip() for t in go("tags").split(",")]
        )
        self.title = go("title")
        self.description = go("description")
        self.author = go("creator")
        self.publisher = go("publisher")
        self.name = go("name")

        # directory setup
        self.output_dir = pathlib.Path(go("output_dir")).expanduser().resolve()
        if go("tmp_dir"):
            pathlib.Path(go("tmp_dir")).mkdir(parents=True, exist_ok=True)
        self.build_dir = pathlib.Path(tempfile.mkdtemp(dir=go("tmp_dir")))

        # debug/developer options
        self.concurrency = go("concurrency")
        self.keep_build_dir = go("keep_build_dir")
        self.debug = go("debug")

        # jinja2 environment setup
        self.jinja2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)), autoescape=True
        )

    @property
    def templates_dir(self):
        return ROOT_DIR.joinpath("templates")

    def add_local_files(self, root_path, folder):
        """ recursively add local files from {folder} starting at {path} """
        for fpath in folder.iterdir():
            path = "/".join([root_path, fpath.name])
            if fpath.is_file():
                self.creator.add_item_for(path=path, title="", fpath=fpath)
            else:
                self.add_local_files(path, fpath)

    def process_all_nodes(self, root_id, concurrency):
        """Loop on content nodes to create zim entries from kolibri DB

        this is a blocking step that uses concurrency"""
        q = queue.Queue()

        # fill queue with (node_id, kind) tuples
        for row in self.db.get_rows(
            "SELECT id, kind FROM content_contentnode "
            "WHERE available=? AND channel_id=?",
            (1, self.channel_id),
        ):
            q.put_nowait(tuple(row))

        # create {concurrency} threads to consume and process the queue via .add_node()
        for _ in range(concurrency):
            threading.Thread(
                target=worker_wrapper,
                args=(self.add_node, q),
                daemon=True,
            ).start()

        q.join()

    def add_node(self, item):
        """ process a content node from the tuple in queue """
        node_id, kind = item
        # check if we have a handler for this {kind} of node
        handler = getattr(self, f"add_{kind}_node", None)
        if handler:
            # add thumbnail to zim if there's one for this node
            thumbnail = self.db.get_node_thumbnail(node_id)
            if thumbnail:
                self.funnel_file(thumbnail["id"], thumbnail["ext"])
            # fire the add_{kind}_node() method which will actually process it
            handler(node_id)

    def funnel_file(self, fid, fext):
        """ directly add a Kolibri file to the ZIM using same name """
        url, fname = get_kolibri_url_for(fid, fext)
        with self.creator_lock:
            self.creator.add_item(URLItem(url=url, path=fname))
        logger.debug(f"Added direct file {fname}")

    def add_topic_node(self, node_id):
        """Build and add the HTML page for a single topic node

        Topic nodes are used only for hierarchy and solely contains metadata"""

        # fetch details including parents for breadcrumb and children to link to
        node = self.db.get_node(node_id, with_parents=True, with_children=True)

        html = self.jinja2_env.get_template("topic.html").render(
            node_id=node_id,
            title=node["title"],
            author=node["author"],
            children=node["children"],
            children_count=node["children_count"],
            parents=node["parents"],
            parents_count=node["parents_count"],
        )
        with self.creator_lock:
            self.creator.add_item_for(
                path=node_id, title=node["title"], content=html, mimetype="text/html"
            )
        logger.debug(f"added topic #{node_id}")

    def add_video_node(self, node_id):
        """Add content from this `video` node to zim

        video node is composed of (1) or (2) videos files and optional subtitle files
        video files are at most one of each `high_res_video` or `low_res_video`
        subtitle files (`video_subtitle`) are VTT files and are only limited by the
        number of language to select from in kolibri studio"""
        raise NotImplementedError("video nodes not supported")

    def add_audio_node(self, node_id):
        """Add content from this `audio` node to zim

        audio node are composed of a single mp3 file"""
        raise NotImplementedError("audio nodes not supported")

    def add_exercise_node(self, node_id):
        """Add content from this `exercise` node to zim

        exercise node is composed of a single perseus file

        a perseus file is a ZIP containing an exercise.json entrypoint and other files

        we'd solely add the perseus file in the ZIM along with the perseus reader from
        https://github.com/Khan/perseus"""
        raise NotImplementedError("exercise nodes not supported")

    def add_document_node(self, node_id):
        """Add content from this `document` node to zim

        document node is composed of one main (`priority` 1) file and
        an optionnal (`priority` 2) file
        Format for each is either `pdf` (`document` preset) or `epub` (`epub` preset)


        - add the actual PDF/epub files to zim at /{node_id}.{ext} (files' IDs)
        - PDF: an HTML redirect at /{node_id} (file) to PDF.js viewer pointing to it
        - EPUB: an HTML redirect at /{node_id} (file) to epub.js viewer pointing to it
        - for the priority 1, a redirect from /{node_id} to the file's HTML
        - for the priority 2, a redirect from /{node_id}/alt to the file's HTML

        # TODO: add support for epub.js
        """

        # record the actual document
        files = self.db.get_node_files(node_id, thumbnail=False)
        if not files:
            return

        files = list(files)
        for file in files:
            self.funnel_file(file["id"], file["ext"])

        # filename = ".".join(tuple(file))
        node = self.db.get_node(node_id)

        def add_pdf_helper(file):
            # create an accessible page for this content
            filename = f'{file["id"]}.{file["ext"]}'
            html = self.jinja2_env.get_template("pdf_redirect.html").render(
                node_id=node_id,
                filename=filename,
                target=f"./assets/pdfjs/web/viewer.html?file=../../../{filename}",
                title=node["title"],
            )
            with self.creator_lock:
                self.creator.add_item_for(
                    path=file["id"],
                    title=node["title"],
                    content=html,
                    mimetype="text/html",
                )

        def add_epub_helper(file):
            """ create an epub.js viewer (hopefuly) """
            filename = f'{file["id"]}.{file["ext"]}'
            html = self.jinja2_env.get_template("epub.html").render(
                node_id=node_id,
                filename=filename,
                title=node["title"],
            )
            with self.creator_lock:
                self.creator.add_item_for(
                    path=file["id"],
                    title=node["title"],
                    content=html,
                    mimetype="text/html",
                )

        for file in files:
            if file["ext"] == "pdf":
                add_pdf_helper(file)
            if file["ext"] == "epub":
                add_epub_helper(file)

        # add redirect to main file's helper
        with self.creator_lock:
            self.creator.add_redirect(path=node_id, target_path=files[0]["id"])

        # add redirect to priority2 file's helper if present
        if len(files) > 1:
            with self.creator_lock:
                self.creator.add_redirect(
                    path=f"{node_id}/alt", target_path=files[1]["id"]
                )

    def add_html5_node(self, node_id):
        """Add content from this `html5` node to zim

        html5 node is single ZIP file containing a standalone HTML app
        which entrypoint is a file named index.html

        we extract and add each file from the ZIP to /{node_id}/

        Note: Studio doesn't enforce the mandatory index.html, thus allowing invalid
        html5 app (unreachable)"""

        file = self.db.get_node_file(node_id, thumbnail=False)
        if not file:
            return

        # download ZIP file to memory
        ark_url, ark_name = get_kolibri_url_for(file["id"], file["ext"])
        ark_data = io.BytesIO()
        stream_file(url=ark_url, byte_stream=ark_data)

        # loop over zip members and create an entry for each
        zip_ark = zipfile.ZipFile(ark_data)
        for ark_member in zip_ark.namelist():
            with self.creator_lock:
                self.creator.add_item_for(
                    path=f"{node_id}/{ark_member}",
                    content=zip_ark.open(ark_member).read(),
                )

    def run(self):
        logger.info(
            f"Starting scraper with:\n"
            f"  channel_id: {self.channel_id}\n"
            f"  build_dir: {self.build_dir}\n"
            f"  output_dir: {self.output_dir}\n"
            f"  video format : {self.video_format}\n"
            f"  low_quality : {self.low_quality}\n"
        )

        logger.info("Download database")
        self.download_db()

        self.sanitize_inputs()
        # display basic stats
        logger.info(
            f"  Starting ZIM creation with:\n"
            f"  filename: {self.fname}\n"
            f"  title: {self.title}\n"
            f"  description: {self.description}\n"
            f"  creator: {self.author}\n"
            f"  publisher: {self.publisher}\n"
            f"  tags: {';'.join(self.tags)}"
        )

        logger.info("Setup Zim Creator")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        root_id = self.db.get_cell(
            "SELECT root_id FROM content_channelmetadata WHERE id=?",
            (self.channel_id,),
        )

        self.creator_lock = threading.Lock()
        self.creator = Creator(
            filename=self.output_dir.joinpath(self.fname),
            main_path=root_id,
            favicon_path="favicon.png",
            language="eng",
            title=self.title,
            description=self.description,
            creator=self.author,
            publisher=self.publisher,
            name=self.name,
            tags=";".join(self.tags),
        ).start()
        self.add_favicon()

        # add static files
        logger.info("Adding local files (assests)")
        self.add_local_files("assets", self.templates_dir.joinpath("assets"))

        logger.info("Processing all nodes")
        self.process_all_nodes(root_id, self.concurrency)

        logger.info("Finishing ZIM file…")
        self.creator.finish()
        logger.info("  done.")

    def download_db(self):
        # download database
        fpath = self.build_dir.joinpath("db.sqlite3")
        logger.debug(f"Downloading database into {fpath.name}…")
        stream_file(
            f"{STUDIO_URL}/content/databases/{self.channel_id}.sqlite3",
            fpath,
        )
        self.db = KolibriDB(fpath)

    def sanitize_inputs(self):
        channel_meta = self.db.get_channel_metadata(self.channel_id)

        # input  & metadata sanitation
        period = datetime.datetime.now().strftime("%Y-%m")
        if self.fname:
            # make sure we were given a filename and not a path
            self.fname = pathlib.Path(self.fname.format(period=period))
            if pathlib.Path(self.fname.name) != self.fname:
                raise ValueError(f"filename is not a filename: {self.fname}")
        else:
            self.fname = f"{self.name}_{period}.zim"

        if not self.title:
            self.title = channel_meta["name"]
        self.title = self.title.strip()

        if not self.description:
            self.description = channel_meta["description"]
        self.description = self.description.strip()

        if not self.author:
            self.author = "Libretexts"
        self.author = self.author.strip()

        if not self.publisher:
            self.publisher = "Openzim"
        self.publisher = self.publisher.strip()

        self.tags = list(set(self.tags + ["_category:other", "kolibri", "_videos:yes"]))

    def add_favicon(self):
        # add channel thumbnail as favicon
        try:
            favicon_prefix, favicon_data = self.db.get_channel_metadata(
                self.channel_id
            )["thumbnail"].split(";base64,", 1)
            favicon_data = base64.standard_b64decode(favicon_data)
            favicon_mime = favicon_prefix.replace("data:", "")
        except Exception as exc:
            logger.warning(f"Unable to extract favicon from DB: {exc}")
            logger.exception(exc)
        else:
            if favicon_mime != "image/png":
                # should convert to PNG
                logger.warning("we shall have converted that favicon to PNG")
            self.creator.add_item_for("favicon.png", content=favicon_data)
