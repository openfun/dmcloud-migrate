#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

import dmmigrate.dmcloud
import dmmigrate.download

def main():
    parser = argparse.ArgumentParser(description="Download all media from an organisation or university")
    parser.add_argument(
        "--fake",
        action="store_true",
        help=(
            """Don't actually download the media files (but perform all other tasks). """
            """You probably want to run this script in fake mode prior to actually downloading all the media files."""
        )
    )
    parser.add_argument("--user-id", help=(
        "DMCloud user ID. If not used, it will be read "
        "from the DMCLOUD_USER_ID environment variable"
    ))
    parser.add_argument("--api-key", help=(
        "DMCloud API key. If not used, it will be read "
        "from the DMCLOUD_API_KEY environment variable"
    ))
    parser.add_argument('-u', '--user', help="Limit downloads to specified user name")
    parser.add_argument("dst", help="Destination directory (will be created if necessary).")
    args = parser.parse_args()

    client = get_client(args.user_id, args.api_key)
    if args.user:
        dmmigrate.download.everything_from_username(client, args.user, args.dst, fake_download=args.fake)
    else:
        dmmigrate.download.everything_from_organisation(client, args.dst, fake_download=args.fake)

def get_client(user_id=None, api_key=None):
    user_id = user_id or os.environ.get('DMCLOUD_USER_ID')
    api_key = api_key or os.environ.get('DMCLOUD_API_KEY')
    if user_id is None:
        raise ValueError("Undefined DMCloud user ID. Define the DMCLOUD_USER_ID environment variable.")
    if api_key is None:
        raise ValueError("Undefined DMCloud API key. Define the DMCLOUD_API_KEY environment variable.")
    return dmmigrate.dmcloud.Client(user_id, api_key)
