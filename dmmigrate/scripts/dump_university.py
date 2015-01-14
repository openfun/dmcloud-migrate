#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

import dmmigrate.download

def main():
    parser = argparse.ArgumentParser(description="Dump all assets from a university")
    parser.add_argument("dmcloud_user_id", help="DMCloud user ID")
    parser.add_argument("dmcloud_api_key", help="DMCloud API key")
    parser.add_argument("dst", help="Destination directory (will be created if necessary).")
    args = parser.parse_args()

    dmmigrate.download.from_university(args.dmcloud_user_id, args.dmcloud_api_key, args.dst)

