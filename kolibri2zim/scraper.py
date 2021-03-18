#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import io
import queue
import shutil
import base64
import zipfile
import pathlib
import datetime
import tempfile
import threading
import concurrent.futures as cf

import jinja2
from zimscraperlib.download import stream_file
from zimscraperlib.zim.creator import Creator
from zimscraperlib.zim.items import URLItem
from zimscraperlib.i18n import find_language_names
from zimscraperlib.video.presets import VideoWebmLow, VideoWebmHigh, VideoMp4Low
from zimscraperlib.video.encoding import reencode

from .constants import ROOT_DIR, getLogger, STUDIO_URL
from .database import KolibriDB

logger = getLogger()
options = [
    "debug",
    "name",
    "use_webm",
    "low_quality",
    "output_dir",
    "fname",
    "title",
    "description",
    "creator",
    "publisher",
    "tags",
    "keep_build_dir",
    "threads",
    "processes",
    "autoplay",
    "channel_id",
    "root_id",
    "tmp_dir",
]


def filename_for(file):
    return f'{file["id"]}.{file["ext"]}'


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
        self.root_id = go("root_id")

        # video-encoding info
        self.use_webm = go("use_webm")
        self.low_quality = go("low_quality")
        self.autoplay = go("autoplay")

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
        self.nb_threads = go("threads")
        self.nb_processes = go("processes")
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
        non_front = ("viewer.html", "epub_embed.html")
        for fpath in folder.iterdir():
            path = "/".join([root_path, fpath.name])
            if fpath.is_file():
                mimetype = "text/html;raw=true" if fpath.name in non_front else None
                self.creator.add_item_for(
                    path=path, title="", fpath=fpath, mimetype=mimetype
                )
                logger.debug(f"adding {path}")
            else:
                self.add_local_files(path, fpath)

    def process_all_nodes(self, nb_threads):
        """Loop on content nodes to create zim entries from kolibri DB

        this is a blocking step that uses nb_threads"""
        q = queue.Queue()

        # add root node
        q.put_nowait((self.db.root["id"], self.db.root["kind"]))

        # fill queue with (node_id, kind) tuples for all root node's descendants
        for node in self.db.get_node_descendants(self.root_id):
            q.put_nowait((node["id"], node["kind"]))

        # create {nb_threads} threads to consume and process the queue via .add_node()
        for _ in range(nb_threads):
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

    def download_to_disk(self, file_id, ext):
        """ download a Kolibri file to the build-dir using its filename """
        url, fname = get_kolibri_url_for(file_id, ext)
        fpath = self.build_dir / fname
        stream_file(url, fpath)
        return fpath

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

        files = self.db.get_node_files(node_id, thumbnail=False)
        if not files:
            return
        files = sorted(files, key=lambda f: f["prio"])
        it = filter(lambda f: f["supp"] == 0, files)

        try:
            # find main video file
            main_video_file = next(it)
        except StopIteration:
            # we have no video file
            return

        try:
            alt_video_file = next(it)
        except StopIteration:
            # we have no supplementary video file (which is OK)
            alt_video_file = None

        # decide which file to keep and what to do with it

        # we'll reencode, using the best file with appropriate preset
        if self.use_webm:
            # download original video
            src = self.download_to_disk(main_video_file["id"], main_video_file["ext"])
            dst = src.with_suffix(".webm")
            video_filename = dst.name
            video_filename_ext = dst.suffix[1:]
            preset = VideoWebmLow if self.low_quality else VideoWebmHigh

            # request conversion
            self.convert_and_add_video_aside(src, dst, preset())

        # we want low-q but no webm yet don't have low_res file, let's reencode
        elif self.low_quality and alt_video_file is None:
            # download original video
            src = self.download_to_disk(main_video_file["id"], main_video_file["ext"])

            # move source file to a new name and swap variables so our target will
            # be the previously source one
            src_ = src.with_suffix(f"{src.suffix}.orig")
            shutil.move(src, src_)
            dst = src
            src = src_

            video_filename = dst.name
            video_filename_ext = dst.suffix[1:]

            # request conversion
            self.convert_and_add_video_aside(src, dst, VideoMp4Low())

        # we want mp4, either in high-q or we have a low_res file to use
        else:
            video_file = alt_video_file if self.low_quality else main_video_file
            self.funnel_file(video_file["id"], video_file["ext"])
            video_filename_ext = video_file["ext"]
            video_filename = filename_for(video_file)

        # prepare list of subtitles for template
        subtitles = []
        for file in filter(lambda f: f["preset"] == "video_subtitle", files):
            self.funnel_file(file["id"], file["ext"])
            try:
                local, english = find_language_names(file["lang"])
            except Exception:
                english = file["lang"]
            finally:
                subtitles.append(
                    {
                        "code": file["lang"],
                        "name": english,
                        "filename": filename_for(file),
                    }
                )

        node = self.db.get_node(node_id, with_parents=True)
        html = self.jinja2_env.get_template("video.html").render(
            node_id=node_id,
            parents=node["parents"],
            parents_count=node["parents_count"],
            video_filename=video_filename,
            video_filename_ext=video_filename_ext,
            title=node["title"],
            subtitles=sorted(subtitles, key=lambda i: i["code"]),
            thumbnail=self.db.get_thumbnail_name(node_id),
            autoplay=self.autoplay,
        )
        with self.creator_lock:
            self.creator.add_item_for(
                path=node_id,
                title=node["title"],
                content=html,
                mimetype="text/html",
            )

    def add_video_upon_completion(self, future):
        """adds the converted video inside this future to the zim

        logs error in case of failure"""
        if future.cancelled():
            return
        src_fpath, dst_fpath = self.videos_futures.get(future)

        try:
            future.result()
        except Exception as exc:
            logger.error(f"Error re-encoding {src_fpath.name}: {exc}")
            logger.exception(exc)
            return

        logger.debug(f"re-encoded {src_fpath.name} successfuly")

        with self.creator_lock:
            self.creator.add_item_for(
                path=dst_fpath.name,
                fpath=dst_fpath,
                delete_fpath=True,
            )

    def convert_and_add_video_aside(self, src_fpath, dest_fpath, preset):
        """add video to the process-based convertion queue"""

        future = self.videos_executor.submit(
            reencode,
            src_path=src_fpath,
            dst_path=dest_fpath,
            ffmpeg_args=preset.to_ffmpeg_args(),
            delete_src=True,
            with_process=False,
            failsafe=False,
        )
        self.videos_futures.update({future: (src_fpath, dest_fpath)})
        future.add_done_callback(self.add_video_upon_completion)

    def add_audio_node(self, node_id):
        """Add content from this `audio` node to zim

        audio node are composed of a single mp3 file"""
        file = self.db.get_node_file(node_id, thumbnail=False)
        if not file:
            return
        self.funnel_file(file["id"], file["ext"])

        node = self.db.get_node(node_id, with_parents=True)
        html = self.jinja2_env.get_template("audio.html").render(
            node_id=node_id,
            parents=node["parents"],
            parents_count=node["parents_count"],
            filename=filename_for(file),
            ext=file["ext"],
            title=node["title"],
            thumbnail=self.db.get_thumbnail_name(node_id),
            autoplay=self.autoplay,
        )
        with self.creator_lock:
            self.creator.add_item_for(
                path=node_id,
                title=node["title"],
                content=html,
                mimetype="text/html",
            )

    def add_exercise_node(self, node_id):
        """Add content from this `exercise` node to zim

        exercise node is composed of a single perseus file

        a perseus file is a ZIP containing an exercise.json entrypoint and other files

        we'd solely add the perseus file in the ZIM along with the perseus reader from
        https://github.com/Khan/perseus"""
        logger.warning(f"[NOT SUPPORTED] not adding exercice node {node_id}")

    def add_document_node(self, node_id):
        """Add content from this `document` node to zim

        document node is composed of one main (`priority` 1) file and
        an optionnal (`priority` 2) file
        Format for each is either `pdf` (`document` preset) or `epub` (`epub` preset)


        - add the actual PDF/epub files to zim at /{node_id}.{ext} (files' IDs)
        - add an HTML page linking to files for download
        - includes an iframe with the appropriate viewer
         - using pdf.js for PDF
         - using epub.js for EPUB
        - add an additional page for the alternate document with its viewer
        """

        def target_for(file):
            filename = filename_for(file)
            if file["ext"] == "pdf":
                return f"./assets/pdfjs/web/viewer.html?file=../../../{filename}"
            if file["ext"] == "epub":
                return f"./assets/epub_embed.html?url=../{filename}"

        # record the actual document
        files = self.db.get_node_files(node_id, thumbnail=False)
        if not files:
            return
        files = sorted(filter(lambda f: f["supp"] == 0, files), key=lambda f: f["prio"])
        it = iter(files)

        try:
            main_document = next(it)
        except StopIteration:
            return

        try:
            alt_document = next(it)
        except StopIteration:
            alt_document = None

        for file in files:
            self.funnel_file(file["id"], file["ext"])
            file["target"] = target_for(file)

        node = self.db.get_node(node_id, with_parents=True)
        # convert generator to list as we might read it twice
        node["parents"] = list(node["parents"])

        # generate page once for each document, changing only `is_alt`
        if alt_document:
            options = [False, True]
        else:
            options = [False]  # main_document only

        for is_alt in options:
            html = self.jinja2_env.get_template("document.html").render(
                node_id=node_id,
                main_document=filename_for(main_document),
                main_document_ext=main_document["ext"],
                alt_document=filename_for(alt_document) if alt_document else None,
                alt_document_ext=alt_document["ext"] if alt_document else None,
                target=target_for(alt_document if is_alt else main_document),
                title=node["title"],
                parents=node["parents"],
                parents_count=node["parents_count"],
                is_alt=is_alt,
            )
            with self.creator_lock:
                path = node_id
                if is_alt:
                    path += "_alt"
                self.creator.add_item_for(
                    path=path,
                    title=node["title"],
                    content=html,
                    mimetype="text/html",
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
            f"  using webm : {self.use_webm}\n"
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

        self.creator_lock = threading.Lock()
        self.creator = Creator(
            filename=self.output_dir.joinpath(self.fname),
            main_path=self.root_id,
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

        # setup a dedicated queue for videos to convert
        self.videos_futures = {}
        self.videos_executor = cf.ProcessPoolExecutor(max_workers=self.nb_processes)

        logger.info("Processing all nodes")
        self.process_all_nodes(self.nb_threads)
        logger.info("Processed all nodes.")

        # await completion of the videos queue
        if self.videos_futures:
            nb_incomplete = sum([1 for f in self.videos_futures if f.running()])
            logger.info(f"Awaiting {nb_incomplete} video convertions to complete…")
        cf.wait(self.videos_futures.keys(), return_when=cf.FIRST_EXCEPTION)
        # properly shutting down the executor should allow processing
        # futures's callbacks (zim addition) as the wait() function
        # only awaits future completion and doesn't include callbacks
        self.videos_executor.shutdown()

        # we shall check wether we completed successfuly or not and fail the scraper
        # accordingly

        logger.info("Finishing ZIM file…")
        self.creator.finish()
        logger.info("  done.")

    def download_db(self):
        """download channel DB from kolibri and initialize DB

        Also sets the root_id with DB-computer value"""
        # download database
        fpath = self.build_dir.joinpath("db.sqlite3")
        logger.debug(f"Downloading database into {fpath.name}…")
        stream_file(
            f"{STUDIO_URL}/content/databases/{self.channel_id}.sqlite3",
            fpath,
        )
        self.db = KolibriDB(fpath, self.root_id)
        self.root_id = self.db.root_id

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
