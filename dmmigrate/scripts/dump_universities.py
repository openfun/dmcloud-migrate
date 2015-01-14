import argparse
import json
import os

import dmmigrate.download

def main():
    parser = argparse.ArgumentParser(description="Dump all assets from all universities")
    parser.add_argument(
        "universities",
        help="Path to a JSON-formatted file that includes all DMCloud API key and user IDs."
    )
    parser.add_argument("dst", help="Destination directory (will be created if necessary).")
    args = parser.parse_args()

    with open(args.universities) as f:
        universities = json.load(f)
    for university in universities:
        university_name = university["name"]
        university_code = university["code"]
        dmcloud_user_id = university['dmcloud_user_id']
        dmcloud_api_key = university['dmcloud_api_key']

        dst = os.path.join(args.dst, university_code)

        print u"Downloading media from {} ({})".format(university_name, university_code)
        dmmigrate.download.from_university(dmcloud_user_id, dmcloud_api_key, dst)
