#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 nu


""" dump a channel content into a folder

    Using a channel_id, download all files it is consisted of and store them in a local
    folder mimicing the studio URLs.

    This allows running kolibri2zim off a local *mirror* of the actual Kolibri Studio
    this saving a lot of bandwidth/time during dev and saving those resources
    on kolibri side as well.

    Just serve build folder via webserver and change STUDIO_URL env for kolibri2zim
    caddy file-server -browse -listen 0.0.0.0:8888 -root build
    STUDIO_URL=http://localhost:8888 kolibri2zim --channel_id xxx

    Uses wget for downloads """

import contextlib
import logging
import multiprocessing as mp
import os
import pathlib
import sqlite3
import subprocess
import sys

STUDIO_DEFAULT_BASE_URL = "https://studio.learningequality.org"
STUDIO_URL = os.getenv("STUDIO_URL", STUDIO_DEFAULT_BASE_URL)
STORAGE_URL = f"{STUDIO_URL}/content/storage"
NB_PARRALLEL_DOWNLOADS = 15

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("dump-remote")


def download_if_missing(url, fpath, fsize=None, *, force=False):
    skipped = (
        fpath.exists()
        and (fsize is not None and os.path.getsize(fpath) == fsize)
        and not force
    )
    if not skipped:
        fpath.unlink(missing_ok=True)
        wget = subprocess.run(
            [
                "/usr/bin/env",
                "wget",
                "-t",
                "5",
                "--retry-connrefused",
                "--random-wait",
                "-O",
                str(fpath),
                "-c",
                url,
            ],
            text=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if wget.returncode != 0:
            logger.error(wget.stdout)
            raise Exception(f"wget exited with retcode {wget.returncode}")
    return not skipped, url, fpath


@contextlib.contextmanager
def get_conn(db_path):
    conn = sqlite3.connect(db_path)
    try:
        yield conn.__enter__()
    except Exception:
        conn.__exit__(*sys.exc_info())
    else:
        conn.__exit__(None, None, None)
    finally:
        conn.close()


def get_single_value(db_path, query):
    with get_conn(db_path) as conn:
        return conn.execute(query).fetchone()[0]


def get_rows(db_path, query):
    with get_conn(db_path) as conn:
        cursor = conn.execute(query)
        rows = cursor.fetchmany()
        while rows:
            yield from rows
            rows = cursor.fetchmany()


def dump(channel_id: str, build_dir: str | None, *, force: bool):
    build_path = pathlib.Path(build_dir or "build")
    logger.info(f"dumping {channel_id} into {build_path}")
    build_path.mkdir(exist_ok=True, parents=True)

    db_path = build_path / "content" / "databases" / f"{channel_id}.sqlite3"
    db_path.parent.mkdir(exist_ok=True, parents=True)
    if db_path.exists() and not force:
        logger.info(f"Reusing existing DB at {db_path}")
    else:
        logger.info("Downloading DB")
        download_if_missing(
            f"{STUDIO_URL}/content/databases/{channel_id}.sqlite3", db_path
        )

    nb_files = get_single_value(db_path, "SELECT COUNT(*) FROM content_file")
    logger.info(f"Looping over all {nb_files} files")

    def on_error(*args, **kwargs):  # noqa: ARG001
        logger.error("Failed to download something")

    def on_success(result):
        downloaded, url, fpath = result
        if downloaded:
            logger.debug(f"Downloaded {fpath}")
        else:
            logger.debug(f"Skipped {fpath}")

    pool = mp.Pool(NB_PARRALLEL_DOWNLOADS)

    for fid, fsize, fext in get_rows(
        db_path, "SELECT id, file_size, extension FROM content_localfile"
    ):
        fname = f"{fid}.{fext}"
        remote_dirs = (fid[0], fid[1])
        remote_path = f"{'/'.join(remote_dirs)}/{fname}"
        local_dir = build_path.joinpath("content/storage").joinpath(*remote_dirs)
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / fname
        pool.apply_async(
            download_if_missing,
            args=(f"{STORAGE_URL}/{remote_path}", local_path, fsize, force),
            callback=on_success,
            error_callback=on_error,
        )
    pool.close()
    pool.join()

    logger.info("Done downloading files")


if __name__ == "__main__":
    args = [sys.argv[idx] if len(sys.argv) >= idx + 1 else None for idx in range(4)]
    _, channel_id, build_dir, force = args

    if not channel_id:
        logger.error("Missing channel ID")
        sys.exit(1)
    force = bool(str(force).lower() in ("true", "force", "yes"))

    dump(channel_id=channel_id, build_dir=build_dir, force=force)
