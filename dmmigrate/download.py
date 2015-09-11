#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from collections import defaultdict
import hashlib
import json
import logging
import os
import requests
from time import time

from . import dmcloud

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.ERROR)


def everything(client, dst_path, username=None, fake_download=False):
    for user in client.iter_organisation_users(username=username):
        user_dst_path = get_user_dst_path(user, dst_path)
        media_json_path = check_media_json(client, user_dst_path)
        for media in iter_media_json(media_json_path):
            check_media(client, media, user_dst_path, fake_download=fake_download)

def estimate_size(client, dst_path, username=None):
    sizes = {}
    for user in client.iter_organisation_users(username=username):
        sizes[user.name] = defaultdict(int)
        user_dst_path = get_user_dst_path(user, dst_path)
        media_json_path = check_media_json(client, user_dst_path)
        for media in iter_media_json(media_json_path):
            media_assets_json_path = check_media_assets_json(client, media, user_dst_path)
            for asset_name, asset_properties in iter_media_assets(media_assets_json_path):
                sizes[user.name][asset_name] += get_asset_size(asset_properties)
    return sizes

def get_user_dst_path(user, base_path):
    return path_join(os.path.normpath(base_path), user.name)

def check_media_json(client, dst_path):
    media_json_path = path_join(dst_path, "media.json")
    if os.path.exists(media_json_path):
        logger.debug("-- Skipping %s", media_json_path)
    else:
        logger.info("-- Creating %s", media_json_path)
        download_media_json(client, media_json_path)
    return media_json_path

def download_media_json(client, dst_path):
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
            yield dmcloud.Media(media["id"], media["title"])

def check_media(client, media, dst_path, fake_download=False):
    media_assets_json_path = check_media_assets_json(client, media, dst_path)
    check_media_assets(media_assets_json_path, fake_download=fake_download)

def check_media_assets_json(client, media, dst_path):
    media_assets_json_path = path_join(dst_path, media.title, media.media_id, "assets.json")
    if os.path.exists(media_assets_json_path):
        logger.debug("---- Skipping %s", media_assets_json_path)
    else:
        logger.info("---- Creating %s", media_assets_json_path)
        download_media_assets_json(client, media, media_assets_json_path)
    return media_assets_json_path

def download_media_assets_json(client, media, dst_path):
    assets = client.get_assets(media)
    ensure_dirname_exists(dst_path)
    with open(dst_path, 'w') as f:
        json_dump(assets, f)

def check_media_assets(media_assets_json_path, fake_download=False):
    dst_directory = os.path.dirname(media_assets_json_path)
    for asset_name, asset_properties in iter_media_assets(media_assets_json_path):
        if asset_name in ["abs", "abs_fa", "live"]:
            # Skip adaptive bitrate streaming or live assets
            continue
        check_media_asset(asset_name, asset_properties, dst_directory, fake_download=fake_download)

def iter_media_assets(media_assets_json_path):
    with open(media_assets_json_path) as f:
        media_assets_json = json.load(f)
    for asset_name, asset_properties in media_assets_json.iteritems():
        yield asset_name, asset_properties

def check_media_asset(asset_name, asset_properties, dst_directory, fake_download=False):
    if should_skip_asset(asset_name, asset_properties):
        return
    extension = get_file_extension(asset_name, asset_properties)
    dst_path = path_join(dst_directory, asset_name + extension)
    if os.path.exists(dst_path):
        logger.debug("---- Skipping %s", dst_path)
    else:
        logger.info("---- Creating %s", dst_path)
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
        file_size = asset_properties["file_size"]
        download_file_safely(download_url, dst_path, checksum=expected_checksum, file_size=file_size)

def get_download_url(asset_properties):
    if "download_url" in asset_properties:
        return asset_properties["download_url"]
    elif asset_properties.get("container") == "JPEG":
        return asset_properties["stream_url"]
    else:
        raise ValueError("Undefined download url")

def download_file_safely(url, dst_path, checksum=None, file_size=None):
    try:
        download_file(url, dst_path, checksum=checksum, file_size=file_size)
    except:
        if os.path.exists(dst_path):
            os.remove(dst_path)
        raise

def download_file(url, dst_path, checksum=None, file_size=None):
    response_checksum = hashlib.md5()
    response_size = 0
    ensure_dirname_exists(dst_path)
    download_time = time()
    with open(dst_path, "wb") as f:
        for content in iter_response_content(url):
            response_checksum.update(content)
            response_size += len(content)
            f.write(content)
    download_speed = (time() - download_time) /((response_size or 1)*1024*1024)
    logger.debug("---- Download speed: %f Mb/s", download_speed)

    if checksum is not None:
        response_checksum = response_checksum.hexdigest()
        if checksum != response_checksum:
            raise ValueError("Checksum mismatch: {} (expected {}) for file {} downloaded from {}".format(
                response_checksum, checksum, dst_path, url
            ))
    if file_size is not None:
        if response_size != file_size:
            raise ValueError("File size mismatch: {} (expected {}) for file {} downloaded from {}".format(
                response_size, file_size, dst_path, url
            ))

def iter_response_content(url):
    response = requests.get(url, stream=True)
    if not response.ok:
        raise ValueError("Download error from {}".format(url))
    for block in response.iter_content(1024):
        if not block:
            break
        yield block

def get_asset_size(asset_properties):
    asset_size = asset_properties.get("file_size", 0)
    #if "streams" in asset_properties:
        #for stream_properties in asset_properties["streams"]:
            #asset_size += get_asset_size(stream_properties)
    return asset_size

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
