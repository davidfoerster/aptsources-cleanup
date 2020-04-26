#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup
from os.path import dirname, join, exists


def parse_description():
    """
    Parse the description in the README file
    """
    readme_fpath = join(dirname(__file__), 'README.md')
    # This breaks on pip install, so check that it exists.
    if exists(readme_fpath):
        with open(readme_fpath, 'r') as f:
            text = f.read()
        return text
    return ''


def read_version(fpath):
    """
    Read the version from the VERSION file
    """
    if exists(fpath):
        with open(fpath, 'r') as file:
            return file.read().strip()
    return None


NAME = 'aptsources-cleanup'
VERSION = read_version('VERSION')


if __name__ == '__main__':
    setup(
        name=NAME,
        version=VERSION,
        author='David Foerster',
        long_description=parse_description(),
        long_description_content_type='text/markdown',
        install_requires=[],
        extras_require={
            'optional': [
                'gitpython',
                'regex',
            ],
        },
        package_dir={'': 'src'},
        packages=find_packages('src'),
        entry_points={
            # the console_scripts entry point creates the aptsources-cleanup executable
            'console_scripts': [
                'aptsources-cleanup = aptsources_cleanup.__main__:main'
            ]
        },
        classifiers=[
            # List of classifiers available at:
            # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        ],
    )
