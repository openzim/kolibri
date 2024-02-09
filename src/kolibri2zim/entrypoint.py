#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import argparse
import sys

from kolibri2zim.constants import NAME, SCRAPER, logger
from kolibri2zim.scraper import Kolibri2Zim


def parse_args(raw_args):
    parser = argparse.ArgumentParser(
        prog=NAME,
        description="Scraper to create ZIM files from Kolibri channels",
    )

    parser.add_argument(
        "--channel-id",
        help="The Kolibri channel ID that you want to scrape",
    )

    parser.add_argument(
        "--root-id",
        help="The node ID (usually Topic) from where to start the scraper. "
        "Defaults to the root of the channel.",
        required=False,
        default=None,
    )

    parser.add_argument(
        "--node-ids",
        help="Comma-separated list of node IDs to process ; root is always processed.",
    )

    parser.add_argument(
        "--name",
        help="ZIM name. Used as identifier and filename (date will be appended)",
        required=True,
    )

    parser.add_argument(
        "--lang",
        help="ZIM Language, used in metadata (should be a ISO-639-3 language code). "
        "If unspecified, scraper will use 'eng'",
        default="eng",
    )

    parser.add_argument(
        "--title",
        help="Custom title for your ZIM. Kolibri channel name otherwise",
    )

    parser.add_argument(
        "--description",
        help="Custom description for your ZIM. Kolibri channel description otherwise",
    )

    parser.add_argument(
        "--long-description",
        help="Custom long description for your ZIM, optional",
    )

    parser.add_argument(
        "--favicon",
        help="URL/path for Favicon. Kolibri channel thumbnail otherwise "
        "or default Kolobri logo if missing",
    )

    parser.add_argument(
        "--about",
        help="URL/path to a single HTML file to use as an about page. "
        "Place everythong inside `body .container` (including stylesheets and scripts) "
        "as only this and your <title> will be merged into the actual about page. "
        "Remember to include images inline using data URL.",
    )

    parser.add_argument(
        "--css",
        help="URL/path to a single CSS file to be included in all pages "
        "(but not on kolibri-html-content ones). "
        "Inlude external resources using data URL.",
    )

    parser.add_argument(
        "--creator",
        help="Name of content creator. Kolibri channel author or “Kolibri” otherwise",
    )

    parser.add_argument(
        "--publisher",
        help="Custom publisher name (ZIM metadata). “openZIM” otherwise",
    )

    parser.add_argument(
        "--tags",
        help="List of comma-separated Tags for the ZIM file. "
        "category:other, kolibri, and _videos:yes added automatically",
    )

    parser.add_argument(
        "--use-webm",
        help="Kolibri videos are in mp4. Choosing webm will require videos to be "
        "re-encoded. Result will be slightly smaller and of lower quality. WebM support"
        " is bundled in the ZIM so videos will be playable on every platform.",
        action="store_true",
        default=False,
        dest="use_webm",
    )

    parser.add_argument(
        "--low-quality",
        help="Uses only the `low_res` version of videos if available. "
        "If not, recompresses using agressive compression.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--autoplay",
        help="Enable autoplay on video articles. "
        "Behavior differs on platforms/browsers.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--output",
        help="Output folder for ZIM file",
        default="/output",
        dest="output_dir",
    )

    parser.add_argument(
        "--tmp-dir",
        help="Path to create temp folder in. Used for building ZIM file. "
        "Receives all data (storage space)",
    )

    parser.add_argument(
        "--zim-file",
        help="ZIM file name (based on --name if not provided)",
        dest="fname",
    )

    parser.add_argument(
        "--keep",
        help="Don't remove build folder on start (for debug/devel)",
        default=False,
        action="store_true",
        dest="keep_build_dir",
    )

    parser.add_argument(
        "--threads",
        help="Number of threads to use to handle nodes concurrently. "
        "Increase to speed-up I/O operations (disk, network). Default: 1",
        default=1,
        type=int,
    )

    parser.add_argument(
        "--processes",
        help="Number of processes to use to handle video compression. "
        "Increase when many CPUs are available and video compression is configured to "
        "use only one CPU. Default: 1",
        default=1,
        type=int,
    )

    parser.add_argument(
        "--optimization-cache",
        help="URL with credentials to S3 for use as optimization cache",
        dest="s3_url_with_credentials",
    )

    parser.add_argument(
        "--dedup-html-files",
        help="Deduplicates in-HTML5 App files by adding each only once and creating "
        "redirects. Usefull for channel with duplicated files (assets) in app. "
        "Caution: can break links if HTML5 app is not completely flat",
        dest="dedup_html_files",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--debug", help="Enable verbose output", action="store_true", default=False
    )

    parser.add_argument(
        "--only-topics",
        help="Debug option to only handle topic nodes",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--version",
        help="Display scraper version and exit",
        action="version",
        version=SCRAPER,
    )
    return parser.parse_args(raw_args)


def main():
    args = parse_args(sys.argv[1:])
    if args.debug:
        for handler in logger.handlers:
            handler.setLevel("DEBUG")

    try:
        scraper = Kolibri2Zim(**dict(args._get_kwargs()))
        sys.exit(scraper.run())
    except Exception as exc:
        logger.error(f"FAILED. An error occurred: {exc}")
        if args.debug:
            logger.exception(exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
