#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

"""
Toned down version of kolibridb.py with modifications to make usage easier and seamless
with the scraper. The functions are kept similar to ensure smooth maintenance in the future
if kolibridb.py gets updated.

See original kolibridb.py here - https://gist.github.com/ivanistheone/ccc3de4f8b115984565370ec74039b53
"""

import json
import pathlib
import sqlite3
from typing import Optional

from zimscraperlib.download import save_large_file

from .constants import SERVERS, getLogger

logger = getLogger()


def download_db_file(
    channel_id: str,
    tmp_dir: pathlib.Path,
    server: Optional[str] = "production",
    update: Optional[bool] = False,
) -> pathlib.Path:
    """
    Download DB file for Kolibri channel `channel_id` from a Studio server.
    """
    db_file_path = pathlib.Path(tmp_dir, channel_id + ".sqlite3")
    if db_file_path.exists() and not update:
        return db_file_path
    if server in SERVERS.keys():
        base_url = SERVERS[server]
    elif "http" in server:
        base_url = server.rstrip("/")
    else:
        raise ValueError("Unrecognized server", server)
    db_file_url = base_url + "/content/databases/" + channel_id + ".sqlite3"
    save_large_file(db_file_url, db_file_path)
    return db_file_path


def dbconnect(db_file_path: pathlib.Path) -> sqlite3.Connection:
    return sqlite3.connect(db_file_path)


def dbex(conn: sqlite3.Connection, query: str) -> list:
    """
    Execure a DB query and return results as a list of dicts.
    """
    cursor = conn.cursor()
    logger.debug(f"Running DB query: {query}")
    cursor.execute(query)
    results = [
        dict(zip([col[0] for col in cursor.description], row))
        for row in cursor.fetchall()
    ]
    return results


def get_channel(conn: sqlite3.Connection) -> list:
    return dbex(conn, "SELECT * FROM content_channelmetadata;")[0]


def get_nodes_by_id(
    conn: sqlite3.Connection,
    attach_files: Optional[bool] = True,
    attach_assessments: Optional[bool] = True,
) -> dict:
    nodes = dbex(conn, "SELECT * FROM content_contentnode;")
    nodes_by_id = {}
    for node in nodes:
        nodes_by_id[node["id"]] = node
    if attach_files:
        # attach all the files associated with each node under the key "files"
        files = get_files(conn)
        for file in files:
            node_id = file["contentnode_id"]
            node = nodes_by_id[node_id]
            if "files" in node:
                node["files"].append(file)
            else:
                node["files"] = [file]
    if attach_assessments:
        assessmentmetadata = get_assessmentmetadata(conn)
        for aim in assessmentmetadata:
            node = nodes_by_id[aim["contentnode_id"]]
            # attach assesment_ids direclty to node to imitate ricecooker/studio
            node["assessment_item_ids"] = json.loads(aim["assessment_item_ids"])
            node["assessmentmetadata"] = {
                "number_of_assessments": aim["number_of_assessments"],
                "mastery_model": aim["mastery_model"],
                "randomize": aim["randomize"],
                "is_manipulable": aim["is_manipulable"],
            }
    return nodes_by_id


def get_files(conn: sqlite3.Connection) -> list:
    return dbex(conn, "SELECT * FROM content_file;")


def get_assessmentmetadata(conn: sqlite3.Connection) -> list:
    return dbex(conn, "SELECT * FROM content_assessmentmetadata;")


def get_tree(conn: sqlite3.Connection) -> dict:
    """
    Return a complete JSON tree of the entire channel.
    """
    nodes_by_id = get_nodes_by_id(conn)
    nodes = nodes_by_id.values()
    sorted_nodes = sorted(
        nodes, key=lambda n: (n["parent_id"] or "0" * 32, n["sort_order"])
    )
    root = sorted_nodes[0]
    for node in sorted_nodes[1:]:
        parent = nodes_by_id[node["parent_id"]]
        if "children" in parent:
            parent["children"].append(node)
        else:
            parent["children"] = [node]
    return root


def get_channel_json(
    channel_id: str,
    json_filepath: pathlib.Path,
    server: Optional[str] = "production",
    update: Optional[bool] = False,
) -> None:
    """
    Convert a channel from Kolibri database file to a JSON tree.
    """

    db_file_path = download_db_file(
        channel_id, server=server, update=update, tmp_dir=json_filepath.parent
    )
    conn = dbconnect(db_file_path)

    kolibri_tree = get_tree(conn)
    conn.close()

    with open(json_filepath, "w") as json_fl:
        json.dump(kolibri_tree, json_fl, indent=4, ensure_ascii=False, sort_keys=True)
    logger.info(f"Channel exported as Kolibri JSON Tree in {json_filepath}")
