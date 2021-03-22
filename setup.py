#! /usr/bin/env python
"""
__setup__.py
Inspired by: https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from os import path
import codecs
import os.path


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


DESCRIPTION = "Reader for lightcurves from the ZTF Public Data Release"
DISTNAME = 'zort'
AUTHOR = 'Michael Medford'
AUTHOR_EMAIL = 'michaelmedford@berkeley.edu'
URL = 'https://github.com/MichaelMedford/zort'
LICENSE = 'MIT'
VERSION = get_version('zort/__init__.py')
DOWNLOAD_URL = 'https://github.com/MichaelMedford/zort/tarball/%s' % VERSION

# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()
LONG_DESCRIPTION_CONTENT_TYPE = 'text/markdown'

setup(name=DISTNAME,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      long_description_content_type=LONG_DESCRIPTION_CONTENT_TYPE,
      license=LICENSE,
      url=URL,
      version=VERSION,
      download_url=DOWNLOAD_URL,
      packages=find_packages(exclude=['contrib', 'docs', 'tests']),
      package_data={'zort': ['data/ZTF_Fields.txt',
                             'data/ZTF_CCD_Layout.tbl']},
      python_requires='>=3.5',
      install_requires=['tqdm',
                        'matplotlib',
                        'numpy',
                        'scipy',
                        'shapely'],
      scripts=['bin/zort-initialize'],
      classifiers=['Intended Audience :: Science/Research',
                   'Programming Language :: Python :: 3.6',
                   'License :: OSI Approved :: MIT License',
                   'Topic :: Scientific/Engineering :: Astronomy',
                   'Operating System :: POSIX',
                   'Operating System :: Unix',
                   'Operating System :: MacOS'],
      project_urls={'Lightcurves': 'https://www.ztf.caltech.edu/page/dr1#12c'}
      )
