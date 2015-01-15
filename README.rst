Dailymotion Cloud migration scripts
===================================

The DmCloud service by Dailymotion is shutting down; this repository provides
python scripts for making a backup of all your DmCloud assets, and eventually
migrating your data to another service.

Install
-------

Always use a virtual environment when installing python dependencies::

    virtualenv venv
    source venv/bin/activate
    pip install git+git://github.com/openfun/dmcloud-migrate.git

Usage
-----

::

    export DMCLOUD_USER_ID="yourdmclouduserid"
    export DMCLOUD_API_KEY="yourdmcloudapikey"

    # Don't actually download the media files:
    dmdownload --fake ./path/to/download/

    # Perform a full backup:
    dmdownload ./path/to/download/ 

    # Perform a full backup for one of your organisation's users:
    dmdownload --user=username ./path/to/download/username/

File system hierarchy
---------------------

Whenever you perform a full backup for your organisation, the files will be
downloaded in the following filesystem hierarchy::

    rootpath/
        username1/
            media.json
            medianame1/
                assets.json
                assetname1
                assetname2
                ...
            medianame2/
                ...
            ...
        username2/
            ...
        ...

For instance, if you have a single user named 'bob', here is a possible file
structure::

    $ dmdownload --user=bob ./dump/

    ./dump/
        bob/
            media.json
            My holiday video (2014)/
                assets.json
                jpeg_thumbnail_medium.jpg
                mp4_h264_aac_hd.mp4
                source.mp4
            Test video 42/
                assets.json
                jpeg_thumbnail_source.jpg
                source.dat
