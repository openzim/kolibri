#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
import os
import pathlib

from zimscraperlib.logging import getLogger as lib_getLogger

from kolibri2zim.__about__ import __version__

ROOT_DIR = pathlib.Path(__file__).parent
NAME = ROOT_DIR.name

VERSION = __version__

SCRAPER = f"{NAME} {VERSION}"

STUDIO_DEFAULT_BASE_URL = "https://studio.learningequality.org"
STUDIO_URL = os.getenv("STUDIO_URL", STUDIO_DEFAULT_BASE_URL)

# when modifiying this list, update list in hatch_build.py as well
JS_DEPS: list[str] = [
    "pdfjs",
    "videojs",
    "ogvjs",
    "bootstrap",
    "bootstrap-icons",
    "perseus",
    "epub.min.js",
    "jszip.min.js",
    "jquery.min.js",
    "videojs-ogvjs.js",
]


logger = lib_getLogger(NAME, logging.INFO)
