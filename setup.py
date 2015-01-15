#! /usr/bin/env python
# -*- coding: utf-8 -*-
from codecs import open as codecs_open
from setuptools import setup, find_packages

def get_long_description():
    with codecs_open('README.rst', encoding='utf-8') as f:
        return f.read()

setup(
        name='dmmigrate',
        version='0.0.1',
        description="Migrate DMCloud videos",
        long_description=get_long_description(),
        classifiers=[],
        keywords='',
        author=u"France Université Numérique",
        author_email='regis@behmo.com',
        url='https://github.com/openfun/dmmigrate',
        license='MIT',
        packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
        include_package_data=True,
        zip_safe=False,
        install_requires=['cloudkey==1.2.7', 'requests'],
        extras_require={
            'test': ['pytest'],
        },
        entry_points={
            'console_scripts': [
                'dmdownload = scripts.download_media:main',
            ]
        },
)

