#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import logging
import os

import dmmigrate.dmcloud
import dmmigrate.download



def download():
    parser = argparse.ArgumentParser(description="Download all media from an organisation or university")
    parser.add_argument(
        "--fake",
        action="store_true",
        help=(
            """Don't actually download the media files (but perform all other tasks). """
            """You probably want to run this script in fake mode prior to actually downloading all the media files."""
        )
    )
    args, client = process_parser(parser)
    dmmigrate.download.everything(client, args.dst, username=args.user, fake_download=args.fake)

def estimate_size():
    parser = argparse.ArgumentParser(description="Estimate media asset size from an organisation or university")
    args, client = process_parser(parser)
    user_sizes = dmmigrate.download.estimate_size(client, args.dst, username=args.user)
    print("Estimated assets size:")
    total = 0
    for username, asset_sizes in sorted(user_sizes.items()):
        user_total = 0
        for asset_name, asset_size in sorted(asset_sizes.items()):
            print_size_line(username, asset_name, asset_size)
            user_total += asset_size
        total += user_total
        print_size_line(username, "TOTAL", user_total)
    print_size_line("", "TOTAL", total)

def print_size_line(username, asset_name, size):
    print("{: <20} {: <30} {: >15} b {: >8.2f} Mb {: >8.2f} Gb".format(
        username, asset_name, size, size*1e-6, size*1e-9
    ))

def process_parser(parser):
    parser.add_argument("--user-id", help=(
        "DMCloud user ID. If not used, it will be read "
        "from the DMCLOUD_USER_ID environment variable"
    ))
    parser.add_argument("--api-key", help=(
        "DMCloud API key. If not used, it will be read "
        "from the DMCLOUD_API_KEY environment variable"
    ))
    parser.add_argument('-u', '--user', help="Limit downloads to specified user name")
    parser.add_argument('-v', '--verbose', action='store_true', help="Set verbose mode")
    parser.add_argument("dst", help="Destination directory (will be created if necessary).")
    args = parser.parse_args()
    set_logger_level(args.verbose)
    client = get_client(args.user_id, args.api_key)
    return args, client

def set_logger_level(verbose_mode):
    if verbose_mode:
        dmmigrate.download.logger.setLevel(logging.DEBUG)

def get_client(user_id=None, api_key=None):
    user_id = user_id or os.environ.get('DMCLOUD_USER_ID')
    api_key = api_key or os.environ.get('DMCLOUD_API_KEY')
    if user_id is None:
        raise ValueError("Undefined DMCloud user ID. Define the DMCLOUD_USER_ID environment variable.")
    if api_key is None:
        raise ValueError("Undefined DMCloud API key. Define the DMCLOUD_API_KEY environment variable.")
    return dmmigrate.dmcloud.Client(user_id, api_key)
