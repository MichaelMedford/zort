#! /usr/bin/env python
"""
__setup__.py
Inspired by: https://github.com/pypa/sampleproject
"""

DESCRIPTION = "Reader for lightcurves from the ZTF Public Data Release"
DISTNAME = 'zort'
AUTHOR = 'Michael Medford'
AUTHOR_EMAIL = 'michaelmedford@berkeley.edu'
URL = 'https://github.com/MichaelMedford/zort'
LICENSE = 'MIT'
VERSION = open('VERSION').readline().strip()
DOWNLOAD_URL = 'https://github.com/MichaelMedford/zort/tarball/%s' % VERSION

from setuptools import setup, find_packages
from os import path

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
                        'numpy'],
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
