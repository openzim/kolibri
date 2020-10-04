#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu


import pathlib
import tempfile

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

        # directory setup
        self.output_dir = pathlib.Path(output_dir).expanduser().resolve()
        if tmp_dir:
            pathlib.Path(tmp_dir).mkdir(parents=True, exist_ok=True)
        self.build_dir = pathlib.Path(tempfile.mkdtemp(dir=tmp_dir))

        # debug/developer options
        self.keep_build_dir = keep_build_dir
        self.debug = debug

    @property
    def templates_dir(self):
        return ROOT_DIR.joinpath("templates")

    @property
    def channel_json_path(self):
        return self.build_dir.joinpath("channel_info.json")

    def run(self):
        logger.info(f"Starting scraper with:\n" f"  video format : {self.video_format}")

        get_channel_json(self.channel_id, self.channel_json_path)

        logger.info("Done Everything")
