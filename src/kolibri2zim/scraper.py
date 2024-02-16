#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import base64
import concurrent.futures as cf
import datetime
import functools
import hashlib
import io
import json
import os
import shutil
import tempfile
import threading
import zipfile
from contextlib import contextmanager
from pathlib import Path

import jinja2
from bs4 import BeautifulSoup
from kiwixstorage import KiwixStorage
from pif import get_public_ip
from zimscraperlib.constants import (
    MAXIMUM_DESCRIPTION_METADATA_LENGTH as MAX_DESC_LENGTH,
)
from zimscraperlib.constants import (
    MAXIMUM_LONG_DESCRIPTION_METADATA_LENGTH as MAX_LONG_DESC_LENGTH,
)
from zimscraperlib.filesystem import get_file_mimetype
from zimscraperlib.i18n import find_language_names
from zimscraperlib.image.convertion import convert_image, create_favicon
from zimscraperlib.image.transformation import resize_image
from zimscraperlib.inputs import handle_user_provided_file
from zimscraperlib.video.presets import VideoMp4Low, VideoWebmHigh, VideoWebmLow
from zimscraperlib.zim.creator import Creator
from zimscraperlib.zim.items import StaticItem

from kolibri2zim.constants import JS_DEPS, ROOT_DIR, STUDIO_URL, logger
from kolibri2zim.database import KolibriDB
from kolibri2zim.debug import (
    ON_DISK_THRESHOLD,
    download_to,
    get_size_and_mime,
    safer_reencode,
)

options = [
    "debug",
    "name",
    "use_webm",
    "low_quality",
    "output_dir",
    "fname",
    "title",
    "description",
    "long_description",
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
    "s3_url_with_credentials",
    "favicon",
    "only_topics",
    "about",
    "css",
    "dedup_html_files",
    "node_ids",
]
NOSTREAM_FUNNEL_SIZE = 1024  # 2**20 * 2  # 2MiB


def filename_for(file):
    return f'{file["id"]}.{file["ext"]}'


def get_kolibri_url_for(file_id: str, ext: str):
    """download URL and filename for a file ID and extension"""
    fname = f"{file_id}.{ext}"
    remote_dirs = (file_id[0], file_id[1])
    remote_path = f"{'/'.join(remote_dirs)}/{fname}"
    return f"{STUDIO_URL}/content/storage/{remote_path}", fname


def read_from_zip(ark, member):
    return ark.open(member).read()


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
            []
            if go("tags") is None
            else [t.strip() for t in go("tags").split(",")]  # pyright: ignore
        )

        self.title = go("title")
        self.description = go("description")
        self.long_description = go("long_description")
        self.author = go("creator")
        self.publisher = go("publisher")
        self.name = go("name")
        self.language = go("lang")

        # customization
        self.favicon = go("favicon")
        self.about = go("about")
        self.css = go("css")

        # directory setup
        self.output_dir = Path(go("output_dir") or "/output").expanduser().resolve()
        if go("tmp_dir"):
            Path(go("tmp_dir")).mkdir(parents=True, exist_ok=True)  # pyright: ignore
        self.build_dir = Path(tempfile.mkdtemp(dir=go("tmp_dir")))

        # performances options
        self.nb_threads = int(go("threads") or 1)
        self.nb_processes = int(go("processes") or 1)
        self.s3_url_with_credentials = go("s3_url_with_credentials")
        self.s3_storage = None
        self.dedup_html_files = go("dedup_html_files")
        self.html_files_cache = []

        # debug/developer options
        self.keep_build_dir = go("keep_build_dir")
        self.debug = go("debug")
        self.only_topics = go("only_topics")
        self.node_ids = (
            None
            if go("node_ids") is None
            else [t.strip() for t in go("node_ids").split(",")]  # pyright: ignore
        )

        # jinja2 environment setup
        self.jinja2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)), autoescape=True
        )

    @property
    def templates_dir(self):
        return ROOT_DIR.joinpath("templates")

    def add_local_files(self, root_path, folder):
        """recursively add local files from {folder} starting at {path}"""
        non_front = ("viewer.html", "epub_embed.html")
        for fpath in folder.iterdir():
            path = "/".join([root_path, fpath.name])
            if fpath.is_file():
                mimetype = "text/html;raw=true" if fpath.name in non_front else None
                self.creator.add_item_for(
                    path=path, title="", fpath=fpath, mimetype=mimetype
                )
                logger.debug(f"Adding {path}")
            else:
                self.add_local_files(path, fpath)

    def populate_nodes_executor(self):
        """Loop on content nodes to create zim entries from kolibri DB"""

        def remove_future(future):
            self.nodes_futures.remove(future)

        def schedule_node(item):
            future = self.nodes_executor.submit(self.add_node, item=item)
            self.nodes_futures.add(future)
            future.add_done_callback(remove_future)

        # schedule root-id
        schedule_node((self.db.root["id"], self.db.root["kind"]))

        # fill queue with (node_id, kind) tuples for all root node's descendants
        for node in self.db.get_node_descendants(self.root_id):
            if self.node_ids is None or node["id"] in self.node_ids:
                schedule_node((node["id"], node["kind"]))

    def add_node(self, item):
        """process a content node from the tuple in queue"""
        node_id, kind = item
        # check if we have a handler for this {kind} of node
        handler = getattr(self, f"add_{kind}_node", None)

        # debug espace
        if self.only_topics and kind != "topic":
            return

        if handler:
            # add thumbnail to zim if there's one for this node
            thumbnail = self.db.get_node_thumbnail(node_id)
            if thumbnail:
                self.funnel_file(thumbnail["id"], thumbnail["ext"])
            # fire the add_{kind}_node() method which will actually process it
            handler(node_id)

    def funnel_file(self, fid, fext):
        """directly add a Kolibri file to the ZIM using same name"""

        url, fname = get_kolibri_url_for(fid, fext)
        size, mimetype = get_size_and_mime(url)

        item_kw = {
            "path": fname,
            "title": "",
            "mimetype": mimetype,
            "delete_fpath": True,
        }

        if not size or size >= ON_DISK_THRESHOLD:
            item_kw["fpath"] = Path(
                tempfile.NamedTemporaryFile(
                    suffix=Path(fname).suffix, delete=False, dir=self.build_dir
                ).name
            )
            download_to(url, item_kw["fpath"])
        else:
            fileobj = io.BytesIO()
            download_to(url, byte_stream=fileobj)
            item_kw["content"] = fileobj.getvalue()
            del fileobj

        with self.creator_lock:
            self.creator.add_item_for(**item_kw)
        logger.debug(f"Added {fname} from Studio")

    def download_to_disk(self, file_id, ext):
        """download a Kolibri file to the build-dir using its filename"""
        url, fname = get_kolibri_url_for(file_id, ext)
        fpath = self.build_dir / fname
        download_to(url, fpath=fpath)
        return fpath

    def funnel_from_s3(self, file_id, path, checksum, preset):
        """whether it could fetch and add the file from S3 cache

        - checks if a cache is configured
        - checks if file is present
        - checks if file is valid (corresponds to same original file)
        - downloads and add to zim

        returns True is all this succeeded, False otherwise"""
        if not self.s3_storage:
            return False

        key = self.s3_key_for(file_id, preset)

        # exit early if we don't have this object in bucket
        if not self.s3_storage.has_object_matching(
            key, meta={"checksum": checksum, "encoder_version": str(preset.VERSION)}
        ):
            return False

        # download file into memory
        fileobj = io.BytesIO()
        try:
            self.s3_storage.download_fileobj(key, fileobj)
        except Exception as exc:
            logger.error(f"failed to download {key} from cache: {exc}")
            logger.exception(exc)
            # make sure we fallback to re-encode
            return False

        # add to zim
        with self.creator_lock:
            kwargs = {
                "path": path,
                "fileobj": fileobj,
                "mimetype": preset.mimetype,
            }
            self.creator.add_item(StaticItem(**kwargs))
        logger.debug(f"Added {path} from S3::{key}")
        return True

    def s3_key_for(self, file_id, preset):
        """compute in-bucket key for file"""
        return f"{file_id[0]}/{file_id[1]}/{file_id}/{type(preset).__name__.lower()}"

    def upload_to_s3(self, key, fpath, **meta):
        """whether it successfully uploaded to cache"""
        if not self.s3_storage:
            return

        logger.debug(f"Uploading {fpath.name} to S3::{key} with {meta}")
        try:
            self.s3_storage.upload_file(fpath, key, meta=meta)
        except Exception as exc:
            logger.error(f"{key} failed to upload to cache: {exc}")
            return False
        return True

    def add_topic_node(self, node_id):
        """Build and add the HTML page for a single topic node

        Topic nodes are used only for hierarchy and solely contains metadata"""

        # fetch details including parents for breadcrumb and children to link to
        node = self.db.get_node(node_id, with_parents=True, with_children=True)

        html = self.jinja2_env.get_template("topic.html").render(
            node_id=node_id, **node
        )
        with self.creator_lock:
            self.creator.add_item_for(
                path=node_id,
                title=node["title"],
                content=html,
                mimetype="text/html",
            )
        logger.debug(f"Added topic #{node_id}")

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
            video_file = next(it)
        except StopIteration:
            # we have no video file
            return

        try:
            alt_video_file = next(it)
        except StopIteration:
            # we have no supplementary video file (which is OK)
            alt_video_file = None

        # now decide which file to keep and what to do with it

        # content_file has a 1:1 rel with content_localfile which is thre
        # *implementation* of the file. We use that local file ID (its checksum)
        # everywhere BUT as S3 cache ID as we want to overwrite the same key
        # should a new version of the localfile for the same file arrives.
        vid = video_file["id"]  # the local file ID (current version)
        vfid = video_file["fid"]  # the file ID in DB (version agnostic)
        vchk = video_file["checksum"]

        # we'll reencode, using the best file with appropriate preset
        if self.use_webm:
            preset = VideoWebmLow() if self.low_quality else VideoWebmHigh()
            src_fname = Path(filename_for(video_file))
            path = str(src_fname.with_suffix(f".{preset.ext}"))
            video_filename_ext = preset.ext
            video_filename = src_fname.with_suffix(f".{video_filename_ext}").name

            # funnel from S3 cache if it is present there
            if not self.funnel_from_s3(vfid, path, vchk, preset):
                # download original video
                src = self.download_to_disk(vid, video_file["ext"])
                dst = src.with_suffix(".webm")

                # request conversion
                self.convert_and_add_video_aside(vfid, src, vchk, dst, path, preset)

        # we want low-q but no webm yet don't have low_res file, let's reencode
        elif self.low_quality and alt_video_file is None:
            preset = VideoMp4Low()
            src_fname = Path(filename_for(video_file))
            path = str(src_fname.with_suffix(f".{preset.ext}"))
            video_filename_ext = preset.ext
            video_filename = src_fname.with_suffix(f".{video_filename_ext}").name

            # funnel from S3 cache if it is present there
            if not self.funnel_from_s3(vfid, path, vchk, preset):
                # download original video
                src = self.download_to_disk(vid, video_file["ext"])

                # move source file to a new name and swap variables so our target will
                # be the previously source one
                src_ = src.with_suffix(f"{src.suffix}.orig")
                shutil.move(src, src_)
                dst = src
                src = src_

                # request conversion
                self.convert_and_add_video_aside(vfid, src, vchk, dst, path, preset)

        # we want mp4, either in high-q or we have a low_res file to use
        else:
            video_file = (
                alt_video_file if self.low_quality and alt_video_file else video_file
            )
            self.funnel_file(video_file["id"], video_file["ext"])
            video_filename = filename_for(video_file)
            video_filename_ext = video_file["ext"]

        # prepare list of subtitles for template
        subtitles = []
        for file in filter(lambda f: f["preset"] == "video_subtitle", files):
            self.funnel_file(file["id"], file["ext"])
            try:
                local, english = find_language_names(file["lang"])
            except Exception:
                english = file["lang"]

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
            video_filename=video_filename,
            video_filename_ext=video_filename_ext,
            subtitles=sorted(subtitles, key=lambda i: i["code"]),
            thumbnail=self.db.get_thumbnail_name(node_id),
            autoplay=self.autoplay,
            **node,
        )
        with self.creator_lock:
            self.creator.add_item_for(
                path=node_id,
                title=node["title"],
                content=html,
                mimetype="text/html",
            )
        logger.debug(f"Added video #{node_id}")

    @contextmanager
    def cleanup_future_once_done(self, future):
        try:
            yield
        finally:
            self.videos_futures.remove(future)

    def video_conversion_completed(
        self, future, src_fname, dest_fpath, path, s3_key, s3_meta
    ):
        """Perform needed duty once video conversion has completed

        - adds the converted video inside this future to the zim
        - upload converted video to cache if configured
        - delete converted video
        """

        with self.cleanup_future_once_done(future):
            if future.cancelled():
                return

            try:
                future.result()
            except Exception as exc:
                logger.error(f"Error re-encoding {src_fname}: {exc}")
                logger.exception(exc)
                return

            logger.debug(f"Re-encoded {src_fname} successfuly")

            kwargs = {
                "path": path,
                "filepath": dest_fpath,
                "mimetype": get_file_mimetype(dest_fpath),
            }

            with self.creator_lock:
                self.creator.add_item(
                    StaticItem(**kwargs),
                    callback=functools.partial(
                        self.converted_video_added_to_zim,
                        dest_fpath=dest_fpath,
                        s3_key=s3_key,
                        s3_meta=s3_meta,
                    ),
                )
            logger.debug(f"Added {path} from re-encoded file")

    def convert_and_add_video_aside(
        self, file_id, src_fpath, src_checksum, dest_fpath, path, preset
    ):
        """add video to the process-based convertion queue"""

        future = self.videos_executor.submit(
            safer_reencode,
            src_path=src_fpath,
            dst_path=dest_fpath,
            ffmpeg_args=preset.to_ffmpeg_args(),
            delete_src=True,
            with_process=False,
            failsafe=False,
        )
        self.videos_futures.add(future)
        future.add_done_callback(
            functools.partial(
                self.video_conversion_completed,
                src_fname=src_fpath.name,
                dest_fpath=dest_fpath,
                path=path,
                s3_key=self.s3_key_for(file_id, preset),
                s3_meta={
                    "checksum": src_checksum,
                    "encoder_version": str(preset.VERSION),
                },
            )
        )

    def converted_video_added_to_zim(self, dest_fpath, s3_key, s3_meta):
        """Perform needed duty once video has been added to the ZIM

        - upload converted video to cache if configured
        - delete converted video
        """

        if self.s3_storage:
            # we shall request s3 upload on the threads pool, only once item has been
            # added to ZIM so it can be removed altogether
            # TODO: submit to a thread executor (to create) instead
            # this is currently called on main-tread.
            self.upload_to_s3(s3_key, dest_fpath, **s3_meta)

        os.unlink(dest_fpath)

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
            filename=filename_for(file),
            ext=file["ext"],
            thumbnail=self.db.get_thumbnail_name(node_id),
            autoplay=self.autoplay,
            **node,
        )
        with self.creator_lock:
            self.creator.add_item_for(
                path=node_id,
                title=node["title"],
                content=html,
                mimetype="text/html",
            )
        logger.debug(f"Added audio #{node_id}")

    def add_exercise_node(self, node_id):
        """Add content from this `exercise` node to zim

        exercise node is composed of a single perseus file.
        a perseus file is a ZIP containing an exercise.json entrypoint and other files
        we extract and add the individual exercises as standalone HTML files dependent
        on standalone version of perseus reader from https://github.com/Khan/perseus"""

        # find perseus file (should be a single one)
        files = self.db.get_node_files(node_id, thumbnail=False)
        if not files:
            return
        files = sorted(files, key=lambda f: f["prio"])
        perseus_file = next(filter(lambda f: f["supp"] == 0, files))

        # download persus file
        perseus_url, perseus_name = get_kolibri_url_for(
            perseus_file["id"], perseus_file["ext"]
        )
        perseus_data = io.BytesIO()
        download_to(perseus_url, byte_stream=perseus_data)

        # read JSON manifest from perseus file
        zip_ark = zipfile.ZipFile(perseus_data)
        manifest_name = "exercise.json"
        if manifest_name not in zip_ark.namelist():
            logger.error(f"Excercise node without {manifest_name}")
            return
        manifest = json.loads(read_from_zip(zip_ark, manifest_name))

        # copy exercise content, rewriting internal paths
        # all internal resources to be stored under {node_id}/ prefix
        assessment_items = []
        for assessment_item in manifest.get("all_assessment_items", []):
            item_path = f"{assessment_item}.json"
            if item_path in zip_ark.namelist():
                perseus_content = read_from_zip(zip_ark, item_path).decode("utf-8")
                perseus_content = perseus_content.replace(
                    r"web+graphie:${☣ LOCALPATH}", f"web+graphie:./{node_id}"
                )
                perseus_content = perseus_content.replace(
                    r"${☣ LOCALPATH}", f"./{node_id}"
                )
                assessment_items.append(perseus_content)

        # add all support files to ZIM
        for ark_member in zip_ark.namelist():
            if ark_member == manifest_name:
                continue

            path = f"{node_id}/{ark_member}"
            with self.creator_lock:
                self.creator.add_item_for(
                    path=path,
                    title="",
                    content=read_from_zip(zip_ark, ark_member),
                )
            logger.debug(f"Added exercise support file {path}")

        # prepare and add exercise HTML article
        node = self.db.get_node(node_id, with_parents=True, with_children=False)
        html = self.jinja2_env.get_template("perseus_exercise.html").render(
            node_id=node_id,
            perseus_content=f"[{', '.join(assessment_items)}]",
            questions_count=str(len(assessment_items)),
            **node,
        )
        with self.creator_lock:
            self.creator.add_item_for(
                path=node_id,
                title=node["title"],
                content=html,
                mimetype="text/html",
            )
        logger.debug(f"Added exercise node #{node_id}")

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
                is_alt=is_alt,
                **node,
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
        logger.debug(f"Added document #{node_id}")

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
        download_to(url=ark_url, byte_stream=ark_data)

        # loop over zip members and create an entry (or redir. for each if using dedup)
        zip_ark = zipfile.ZipFile(ark_data)
        for ark_member in zip_ark.namelist():
            if not self.dedup_html_files:
                with self.creator_lock:
                    self.creator.add_item_for(
                        path=f"{node_id}/{ark_member}",
                        content=zip_ark.open(ark_member).read(),
                    )
                continue

            # calculate hash of file and add entry if not in zim already
            content = zip_ark.open(ark_member).read()
            content_hash = hashlib.md5(content).hexdigest()  # nosec # noqa: S324

            if content_hash not in self.html_files_cache:
                self.html_files_cache.append(content_hash)
                with self.creator_lock:
                    self.creator.add_item_for(
                        path=f"html5_files/{content_hash}",
                        content=content,
                    )

            # add redirect to the unique sum-based entry for that file's path
            with self.creator_lock:
                self.creator.add_redirect(
                    path=f"{node_id}/{ark_member}",
                    target_path=f"html5_files/{content_hash}",
                )

        logger.debug(f"Added HTML5 node #{node_id}")

    def run(self):
        if self.s3_url_with_credentials and not self.s3_credentials_ok():
            raise ValueError("Unable to connect to Optimization Cache. Check its URL.")

        s3_msg = (
            f"  using cache: {self.s3_storage.url.netloc} "
            f"with bucket: {self.s3_storage.bucket_name}"
            if self.s3_storage
            else ""
        )
        logger.info(
            f"Starting scraper with:\n"
            f"  channel_id: {self.channel_id}\n"
            f"  build_dir: {self.build_dir}\n"
            f"  output_dir: {self.output_dir}\n"
            f"  using webm : {self.use_webm}\n"
            f"  low_quality : {self.low_quality}\n"
            f"{s3_msg}"
        )

        self.ensure_js_deps_are_present()

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
            f"  language: {self.language}\n"
            f"  tags: {';'.join(self.tags)}"
        )

        logger.info("Retrieving favicon")
        self.retrieve_favicon()

        logger.info("Setup Zim Creator")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.creator_lock = threading.Lock()
        if not self.root_id:
            logger.error("Missing root id")
            return 1
        if not self.title:
            logger.error("Missing title")
            return 1
        if not self.description:
            logger.error("Missing description")
            return 1
        if not self.author:
            logger.error("Missing author")
            return 1
        if not self.publisher:
            logger.error("Missing publisher")
            return 1
        self.creator = Creator(
            filename=self.output_dir.joinpath(self.clean_fname),
            main_path=self.root_id,
            ignore_duplicates=True,
        )
        self.creator.config_metadata(
            Name=self.name,  # pyright: ignore[reportArgumentType]
            Language=self.language,  # pyright: ignore[reportArgumentType]
            Title=self.title,
            Description=self.description,
            LongDescription=self.long_description,
            Creator=self.author,
            Publisher=self.publisher,
            Date=datetime.date.today(),
            Illustration_48x48_at_1=self.favicon_48_fpath.read_bytes(),
        )
        self.creator.start()

        succeeded = False
        try:
            self.add_favicon()
            self.add_custom_about_and_css()

            # add static files
            logger.info("Adding local files (assets)")
            self.add_local_files("assets", self.templates_dir.joinpath("assets"))

            # setup queue for nodes processing
            self.nodes_futures = set()
            self.nodes_executor = cf.ThreadPoolExecutor(max_workers=self.nb_threads)

            # setup a dedicated queue for videos to convert
            self.videos_futures = set()
            self.videos_executor = cf.ProcessPoolExecutor(max_workers=self.nb_processes)

            logger.info("Starting nodes processing")
            self.populate_nodes_executor()

            # await completion of all futures (nodes and videos)
            result = cf.wait(
                self.videos_futures | self.nodes_futures,
                return_when=cf.FIRST_EXCEPTION,
            )
            self.nodes_executor.shutdown()
            # properly shutting down the executor should allow processing
            # futures's callbacks (zim addition) as the wait() function
            # only awaits future completion and doesn't include callbacks
            self.videos_executor.shutdown()

            succeeded = (
                not result.not_done
                and sum([1 if fs.exception() else 0 for fs in result.done]) == 0
            )

            # DEBUG: raise first exception
            if not succeeded and result.done:
                logger.info(
                    f"FAILURE not_done={len(result.not_done)} done={len(result.done)}"
                )
                for future in result.done:
                    if future.exception():
                        raise future.exception()  # pyright:ignore
        except KeyboardInterrupt:
            self.creator.can_finish = False
            logger.error("KeyboardInterrupt, exiting.")
        except Exception as exc:
            # request Creator not to create a ZIM file on finish
            self.creator.can_finish = False
            logger.error(f"Interrupting process due to error: {exc}")
            logger.exception(exc)
        finally:
            if succeeded:
                logger.info("Finishing ZIM file…")
            # we need to release libzim's resources.
            # currently does nothing but crash if can_finish=False but that's awaiting
            # impl. at libkiwix level
            with self.creator_lock:
                self.creator.finish()

        if not self.keep_build_dir:
            logger.info("Removing build folder")
            shutil.rmtree(self.build_dir, ignore_errors=True)

        return 0 if succeeded else 1

    def s3_credentials_ok(self):
        logger.info("testing S3 Optimization Cache credentials")
        self.s3_storage = KiwixStorage(self.s3_url_with_credentials)
        if not self.s3_storage.check_credentials(
            list_buckets=True, bucket=True, write=True, read=True, failsafe=True
        ):
            logger.error("S3 cache connection error testing permissions.")
            logger.error(f"  Server: {self.s3_storage.url.netloc}")
            logger.error(f"  Bucket: {self.s3_storage.bucket_name}")
            logger.error(f"  Key ID: {self.s3_storage.params.get('keyid')}")
            logger.error(f"  Public IP: {get_public_ip()}")
            return False
        return True

    def download_db(self):
        """download channel DB from kolibri and initialize DB

        Also sets the root_id with DB-computer value"""
        # download database
        fpath = self.build_dir.joinpath("db.sqlite3")
        logger.debug(f"Downloading database into {fpath.name}…")
        download_to(
            f"{STUDIO_URL}/content/databases/{self.channel_id}.sqlite3",
            fpath,
        )
        self.db = KolibriDB(fpath, self.root_id)
        self.root_id = self.db.root_id

    def sanitize_inputs(self):
        channel_meta = self.db.get_channel_metadata(self.channel_id)

        # input  & metadata sanitation
        period = datetime.date.today().strftime("%Y-%m")
        if self.fname:
            # make sure we were given a filename and not a path
            fname_path = Path(str(self.fname).format(period=period))
            if Path(fname_path.name) != fname_path:
                raise ValueError(f"filename is not a filename: {self.fname}")
            self.clean_fname = str(fname_path)
        else:
            self.clean_fname = f"{self.name}_{period}.zim"

        if not self.title:
            self.title = channel_meta["name"]
        self.title = self.title.strip()

        if self.description and len(self.description) > MAX_DESC_LENGTH:
            raise ValueError(
                f"Description too long ({len(self.description)}>{MAX_DESC_LENGTH})"
            )
        if self.long_description and len(self.long_description) > MAX_LONG_DESC_LENGTH:
            raise ValueError(
                f"LongDescription too long ({len(self.long_description)}"
                f">{MAX_LONG_DESC_LENGTH})"
            )

        kolibri_desc = channel_meta["description"].strip()
        if not self.long_description and len(kolibri_desc) > MAX_DESC_LENGTH:
            self.long_description = kolibri_desc[0:MAX_LONG_DESC_LENGTH]
            if len(kolibri_desc) > MAX_LONG_DESC_LENGTH:
                self.long_description = self.long_description[:-1] + "…"
        if not self.description:
            self.description = kolibri_desc[0:MAX_DESC_LENGTH]
            if len(kolibri_desc) > MAX_DESC_LENGTH:
                self.description = self.description[:-1] + "…"

        if not self.author:
            self.author = channel_meta["author"] or "Kolibri"
        self.author = self.author.strip()

        if not self.publisher:
            self.publisher = "openZIM"
        self.publisher = self.publisher.strip()

        self.tags = list({*self.tags, "_category:other", "kolibri", "_videos:yes"})

    def retrieve_favicon(self):
        favicon_orig = self.build_dir / "favicon"
        # if user provided a custom favicon, retrieve that
        if self.favicon:
            handle_user_provided_file(source=self.favicon, dest=favicon_orig)
        # otherwise, get thumbnail from database
        else:
            # add channel thumbnail as favicon
            try:
                favicon_prefix, favicon_data = self.db.get_channel_metadata(
                    self.channel_id
                )["thumbnail"].split(";base64,", 1)
                favicon_data = base64.standard_b64decode(favicon_data)
                # favicon_mime = favicon_prefix.replace("data:", "")
                with open(favicon_orig, "wb") as fh:
                    fh.write(favicon_data)
                del favicon_data
            except Exception as exc:
                logger.warning("Unable to extract favicon from DB; using default")
                logger.exception(exc)

                # use a default favicon
                handle_user_provided_file(
                    source=self.templates_dir / "kolibri-logo.png", dest=favicon_orig
                )

        # convert to PNG (might already be PNG but it's OK)
        self.favicon_48_fpath = favicon_orig.with_suffix(".48.png")
        convert_image(favicon_orig, self.favicon_48_fpath)

        self.favicon_96_fpath = favicon_orig.with_suffix(".96.png")
        convert_image(favicon_orig, self.favicon_96_fpath)

        # resize to appropriate size (ZIM uses 48x48 so we double for retina)
        resize_image(self.favicon_48_fpath, width=48, height=48, method="contain")
        resize_image(self.favicon_96_fpath, width=96, height=96, method="contain")

        # generate favicon
        self.favicon_ico_path = favicon_orig.with_suffix(".ico")
        create_favicon(src=self.favicon_96_fpath, dst=self.favicon_ico_path)

    def add_favicon(self):
        self.creator.add_illustration(96, self.favicon_96_fpath.read_bytes())
        self.creator.add_item_for("favicon.png", fpath=self.favicon_96_fpath)
        self.creator.add_item_for("favicon.ico", fpath=self.favicon_ico_path)

    def add_custom_about_and_css(self):
        channel_meta = self.db.get_channel_metadata(self.channel_id)

        if self.about:
            # if user provided a custom about page, use it
            user_provided_file = handle_user_provided_file(
                source=self.about, in_dir=self.build_dir, nocopy=True
            )
            if not user_provided_file:
                title = channel_meta["name"]
                content = None
            else:
                soup = BeautifulSoup(user_provided_file.read_bytes(), "lxml")
                title = soup.find("title")
                if not title:
                    raise Exception("Failed to extract title")
                title = title.text
                content = soup.select("body > .container")
                # we're only interested in the first one
                if isinstance(content, list):
                    content = content[0]
        else:
            title = channel_meta["name"]
            content = None

        html = self.jinja2_env.get_template("about.html").render(
            title=title, content=content, **channel_meta
        )
        with self.creator_lock:
            self.creator.add_item_for(
                path="about",
                title=title,
                content=html,
                mimetype="text/html",
            )
        del html

        # if user provided a custom CSS file, use it
        if self.css:
            user_provided_file = handle_user_provided_file(
                source=self.css, in_dir=self.build_dir, nocopy=True
            )
            if not user_provided_file:
                content = ""
            else:
                content = user_provided_file.read_bytes()
        # otherwise, create a blank one
        else:
            content = ""

        self.creator.add_item_for("custom.css", content=content, mimetype="text/css")
        logger.debug("Added about page and custom CSS")

    def ensure_js_deps_are_present(self):
        for dep in JS_DEPS:
            if not self.templates_dir.joinpath(f"assets/{dep}").exists():
                raise ValueError(
                    "It looks like JS deps have not been installed,"
                    f" {dep} is missing"
                )
