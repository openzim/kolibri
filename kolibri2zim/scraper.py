#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu


import json
import pathlib
import tempfile
import zipfile
import shutil

import jinja2
from zimscraperlib.download import save_large_file
from zimscraperlib.zim import Creator

from .constants import ROOT_DIR, getLogger
from .db_exporter import get_channel_json

logger = getLogger()


class Kolibri2Zim:
    def __init__(
        self,
        debug,
        name,
        video_format,
        low_quality,
        output_dir,
        fname,
        title,
        description,
        creator,
        publisher,
        tags,
        keep_build_dir,
        autoplay,
        channel_id,
        tmp_dir,
    ):

        self.channel_id = channel_id

        # video-encoding info
        self.video_format = video_format
        self.low_quality = low_quality

        # zim params
        self.fname = fname
        self.tags = [] if tags is None else [t.strip() for t in tags.split(",")]
        self.title = title
        self.description = description
        self.creator = creator
        self.publisher = publisher
        self.name = name
        self.creator = None

        # directory setup
        self.output_dir = pathlib.Path(output_dir).expanduser().resolve()
        if tmp_dir:
            pathlib.Path(tmp_dir).mkdir(parents=True, exist_ok=True)
        self.build_dir = pathlib.Path(tempfile.mkdtemp(dir=tmp_dir))

        # debug/developer options
        self.keep_build_dir = keep_build_dir
        self.debug = debug

        # jinja2 environment setup
        self.jinja2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)), autoescape=True
        )

    @property
    def templates_dir(self):
        return ROOT_DIR.joinpath("templates")

    @property
    def channel_json_path(self):
        return self.build_dir.joinpath("channel_info.json")

    def add_files_recursively(self, curr_path, filesystem_path):
        for content in filesystem_path.iterdir():
            if content.is_file():
                if content.suffix == ".css":
                    self.creator.add_css(
                        url=f"{curr_path}{content.name}", fpath=content
                    )
                else:
                    self.creator.add_binary(
                        url=f"{curr_path}{content.name}", fpath=content
                    )
            else:
                self.add_files_recursively(f"{curr_path}{content.name}/", content)

    def add_node_files_to_zim(self, json_dict, curr_path):
        if not json_dict.get("files"):
            logger.debug(f"Node {json_dict['id']} does not have any associated files")
            return
        print(json_dict.get("files"))
        for file_node in json_dict.get("files"):
            file_asset_name = f"{file_node['local_file_id']}.{file_node['extension']}"
            download_path = pathlib.Path(tempfile.mkdtemp(dir=self.build_dir)).joinpath(
                file_asset_name
            )
            save_large_file(
                f"http://studio.learningequality.org/content/storage/{file_asset_name[0]}/{file_asset_name[1]}/{file_asset_name}",
                download_path,
            )
            print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
            if file_node["extension"] in ["zip", "h5p"]:
                with zipfile.ZipFile(download_path, "r") as zipfl:
                    zipfl.extractall(download_path.parent.joinpath("zip_content"))
                print("BEFORE")
                self.add_files_recursively(
                    f"{curr_path}zip_content/",
                    download_path.parent.joinpath("zip_content"),
                )
                print("AFTER")
            else:
                print("BEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                try:
                    self.creator.add_binary(
                        url=f"{curr_path}{download_path.name}", fpath=download_path
                    )
                except Exception as exc:
                    print(exc)
                    print("AFTERRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR")

            # download_path.parent.rmdir()

    def add_video_node_to_zim(self, json_dict, curr_path, path_to_root):
        self.add_node_files_to_zim(json_dict, curr_path)
        video_name = None
        subs = []
        for file_node in json_dict.get("files"):
            if file_node["preset"] in ["high_res_video", "low_res_video"]:
                video_name = f"{file_node['local_file_id']}.{file_node['extension']}"
            if file_node["preset"] == "video_subtitle":
                subs += [
                    {
                        "file": f"{file_node['local_file_id']}.{file_node['extension']}",
                        "code": file_node["lang_id"],
                    }
                ]
        return self.jinja2_env.get_template("video_node.html").render(
            node=json_dict,
            path_to_root=path_to_root,
            video_path=video_name,
            subs=subs,
            format="mp4",
        )

    def add_html_node_to_zim(self, json_dict, curr_path, path_to_root):
        self.add_node_files_to_zim(json_dict, curr_path)
        return self.jinja2_env.get_template("html_node.html").render(
            node=json_dict,
            path_to_root=path_to_root,
        )

    def add_slideshow_node_to_zim(self, json_dict, curr_path, path_to_root):
        self.add_node_files_to_zim(json_dict, curr_path)

    def add_exercise_node_to_zim(self, json_dict, curr_path, path_to_root):
        self.add_node_files_to_zim(json_dict, curr_path)

    def add_document_node_to_zim(self, json_dict, curr_path, path_to_root):
        self.add_node_files_to_zim(json_dict, curr_path)

    def add_h5p_node_to_zim(self, json_dict, curr_path, path_to_root):
        self.add_node_files_to_zim(json_dict, curr_path)
        return self.jinja2_env.get_template("h5p_node.html").render(
            node=json_dict,
            path_to_root=path_to_root,
        )

    def add_audio_node_to_zim(self, json_dict, curr_path, path_to_root):
        self.add_node_files_to_zim(json_dict, curr_path)
        audio_name = None
        audio_thumbnail = None
        for file_node in json_dict.get("files"):
            if file_node["preset"] == "audio":
                audio_name = f"{file_node['local_file_id']}.{file_node['extension']}"
            if file_node["preset"] == "audio_thumbnail":
                audio_thumbnail = (
                    f"{file_node['local_file_id']}.{file_node['extension']}"
                )
        return self.jinja2_env.get_template("audio_node.html").render(
            node=json_dict,
            path_to_root=path_to_root,
            audio_path=audio_name,
            format="mp3",
        )

    def render_topic_node(self, json_dict, curr_path, path_to_root):
        # add html jinja
        html = self.jinja2_env.get_template("tree_node.html").render(
            node=json_dict,
            path_to_root=path_to_root,
        )
        self.creator.add_article(
            url=f"{curr_path}index.html",
            content=html,
            title="Test",
            rewrite_links=True,
        )

    def render_content_node(self, json_dict, curr_path, path_to_root):
        html = None
        contentnode_type = json_dict["kind"]
        if contentnode_type == "video":
            html = self.add_video_node_to_zim(json_dict, curr_path, path_to_root)
        elif contentnode_type == "audio":
            html = self.add_audio_node_to_zim(json_dict, curr_path, path_to_root)
        elif contentnode_type == "html5":
            html = self.add_html_node_to_zim(json_dict, curr_path, path_to_root)
        elif contentnode_type == "h5p":
            html = self.add_h5p_node_to_zim(json_dict, curr_path, path_to_root)
        elif contentnode_type == "slideshow":
            html = self.add_slideshow_node_to_zim(json_dict, curr_path, path_to_root)
        elif contentnode_type == "exercise":
            html = self.add_exercise_node_to_zim(json_dict, curr_path, path_to_root)
        elif contentnode_type == "document":
            html = self.add_document_node_to_zim(json_dict, curr_path, path_to_root)
        else:
            logger.warning(f"Unsupported content node type: {contentnode_type}")
        if html is not None:
            self.creator.add_article(
                url=f"{curr_path}index.html",
                content=html,
                title="Test",
                rewrite_links=True,
            )

    def create_nodes(self, json_dict, curr_path, path_to_root):
        if json_dict["kind"] == "topic":
            self.render_topic_node(json_dict, curr_path, path_to_root)
        else:
            self.render_content_node(json_dict, curr_path, path_to_root)
        if json_dict.get("children"):
            for node in json_dict["children"]:
                self.create_nodes(
                    node, f"{curr_path}{node['id']}/", path_to_root + "../"
                )

    def run(self):
        logger.info(f"Starting scraper with:\n" f"  video format : {self.video_format}")

        json_dict = None
        get_channel_json(self.channel_id, self.channel_json_path)
        with open(self.channel_json_path, "r") as f:
            json_dict = json.load(f)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.creator = Creator(
            filename=self.output_dir.joinpath("test.zim"),
            main_page="index.html",
            language="eng",
        )
        self.create_nodes(json_dict, "", "")

        # copy contents of the assets folder
        self.add_files_recursively("assets/", self.templates_dir.joinpath("assets"))
        self.creator.close()

        logger.info("Done Everything")
