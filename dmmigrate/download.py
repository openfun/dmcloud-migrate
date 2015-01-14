#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import codecs
import hashlib
import json
import os
import requests
import sys

from . import cloudkeyclient

utf8_writer = codecs.getwriter("utf-8")
sys.stdout = utf8_writer(sys.stdout)
sys.stderr = utf8_writer(sys.stderr)


def from_organisation(dm_cloud_user_id, dm_cloud_api_key, dst_path, fake_download=False):
    dst_path = os.path.normpath(dst_path)
    client = cloudkeyclient.Client(dm_cloud_user_id, dm_cloud_api_key)
    for user in client.iter_users():
        media_json_path = check_media_json(client, user, dst_path)
        for media in iter_media_json(media_json_path):
            check_media(client, user, media, dst_path, fake_download=fake_download)

def from_university(dm_cloud_user_id, dm_cloud_api_key, path):
    client = cloudkeyclient.Client(dm_cloud_user_id, dm_cloud_api_key)
    for _media in client.iter_media():
        # TODO
        pass

def check_media_json(client, user, dst_path):
    media_json_path = path_join(dst_path, user.name, "media.json")
    if os.path.exists(media_json_path):
        print("-- Skipping", media_json_path)
    else:
        print("-- Creating", media_json_path)
        download_media_json(client, user, media_json_path)
    return media_json_path

def download_media_json(client, user, dst_path):
    client.act_as_user(user)
    media = [
        {
            "id": media.media_id,
            "title": media.title
        }
        for media in client.iter_media()
    ]
    ensure_dirname_exists(dst_path)
    with open(dst_path, 'w') as f:
        json_dump(media, f)

def iter_media_json(path):
    with open(path) as f:
        for media in json.load(f):
            yield cloudkeyclient.Media(media["id"], media["title"])

def check_media(client, user, media, dst_path, fake_download=False):
    media_assets_json_path = check_media_assets_json(client, user, media, dst_path)
    check_media_assets(media_assets_json_path, fake_download=fake_download)

def check_media_assets_json(client, user, media, dst_path):
    media_assets_json_path = path_join(dst_path, user.name, media.title, "assets.json")
    if os.path.exists(media_assets_json_path):
        print("---- Skipping", media_assets_json_path)
    else:
        print("---- Creating", media_assets_json_path)
        download_media_assets_json(client, user, media, media_assets_json_path)
    return media_assets_json_path

def download_media_assets_json(client, user, media, dst_path):
    client.act_as_user(user)
    assets = client.get_assets(media)
    ensure_dirname_exists(dst_path)
    with open(dst_path, 'w') as f:
        json_dump(assets, f)

def check_media_assets(media_assets_json_path, fake_download=False):
    dst_directory = os.path.dirname(media_assets_json_path)
    with open(media_assets_json_path) as f:
        media_assets_json = json.load(f)
    for asset_name, asset_properties in media_assets_json.iteritems():
        if asset_name in ["abs", "abs_fa", "live"]:
            # Skip adaptive bitrate streaming or live assets
            continue
        check_media_asset(asset_name, asset_properties, dst_directory, fake_download=fake_download)

def check_media_asset(asset_name, asset_properties, dst_directory, fake_download=False):
    if should_skip_asset(asset_name, asset_properties):
        return
    extension = get_file_extension(asset_name, asset_properties)
    dst_path = path_join(dst_directory, asset_name + extension)
    if os.path.exists(dst_path):
        print("---- Skipping", dst_path)
    else:
        print("---- Creating", dst_path)
        download_media_asset(asset_name, asset_properties, dst_path, fake_download=fake_download)
    return dst_path

def should_skip_asset(asset_name, asset_properties):
    if "container" not in asset_properties and asset_properties["status"] == "error":
        return True
    return False

def get_file_extension(asset_name, asset_properties):
    if asset_name == "source":
        return "." + asset_properties["file_extension"]

    container = get_container(asset_name, asset_properties)
    return get_file_extension_for_container(container)

def get_container(asset_name, asset_properties):
    container = asset_properties.get("container")
    if container is None:
        raise ValueError("No container in {}".format(asset_name))
    return container

def get_file_extension_for_container(container):
    extensions = {
        #"AVI": "avi",
        #"Flash Video": "flv",
        "JPEG": "jpg",
        #"Matroska": "mkv",
        "MPEG-4": "mp4",
        #"MPEG-PS": "mpeg",
        #"QuickTime": "mov",
        #"Windows Media": "asf",
        #"XAVC": "mp4",
    }
    extension = extensions.get(container)
    if extension is None:
        raise ValueError("Unknown container: {}".format(container))
    return "." + extension


def download_media_asset(asset_name, asset_properties, dst_path, fake_download=False):
    download_url = get_download_url(asset_properties)

    if not fake_download:
        expected_checksum = asset_properties["checksum"] if asset_name == "source" else None
        download_file(download_url, dst_path, checksum=expected_checksum)

def get_download_url(asset_properties):
    if "download_url" in asset_properties:
        return asset_properties["download_url"]
    elif asset_properties.get("container") == "JPEG":
        return asset_properties["stream_url"]
    else:
        raise ValueError("Undefined download url")

def download_file(url, dst_path, checksum=None):
    content = download_from(url)
    if checksum is not None:
        response_checksum = hashlib.md5(content).hexdigest()
        if checksum != response_checksum:
            raise ValueError("Checksum mismatch: {} (expected {}) for file {} downloaded from {}".format(
                response_checksum, checksum, dst_path, url
            ))

    ensure_dirname_exists(dst_path)

    with open(dst_path, "wb") as f:
        f.write(content)

def download_from(url):
    response = requests.get(url, stream=True)
    if not response.ok:
        raise ValueError("Download error from {}".format(url))
    content = ''
    for block in response.iter_content(1024):
        if not block:
            break
        content += block
    return content

def path_join(basepath, *paths):
    valid_paths = [valid_path(path) for path in paths]
    return os.path.join(basepath, *valid_paths)

def valid_path(path):
    return path.replace("..", "__").replace('/', '__')

def ensure_dirname_exists(path):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def json_dump(obj, f):
    return json.dump(obj, f, indent=2, sort_keys=True)

def print_error(message):
    print(message, file=sys.stderr)
