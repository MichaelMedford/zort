#! /usr/bin/env python
"""
__setup__.py
"""

DESCRIPTION = "Read lightcurves from the ZTF Public Data Release  "
LONG_DESCRIPTION = """ Read lightcurves from the ZTF Public Data Release """

DISTNAME = 'zort'
AUTHOR = 'Michael Medford'
MAINTAINER = 'Michael Medford'
MAINTAINER_EMAIL = 'michaelmedford@berkeley.edu'
URL = 'https://github.com/MichaelMedford/zort'
LICENSE = 'MIT'
VERSION = open('zort/VERSION').readline().strip()
DOWNLOAD_URL = 'https://github.com/MichaelMedford/zort/tarball/%s' % VERSION

try:
    from setuptools import setup, find_packages
    _has_setuptools = True
except ImportError:
    from distutils.core import setup
_has_setuptools = False

if __name__ == "__main__":

    if _has_setuptools:
        packages = find_packages()
    else:
        # This should be updated if new submodules are added
        packages = ['zort']

    setup(name=DISTNAME,
          author=AUTHOR,
          author_email=MAINTAINER_EMAIL,
          maintainer=MAINTAINER,
          maintainer_email=MAINTAINER_EMAIL,
          description=DESCRIPTION,
          long_description=LONG_DESCRIPTION,
          license=LICENSE,
          url=URL,
          version=VERSION,
          download_url=DOWNLOAD_URL,
          packages=packages,
          package_data={'': ['VERSION']},
          include_package_data=True,
          classifiers=[
              'Intended Audience :: Science/Research',
              'Programming Language :: Python :: 3.6',
              'License :: OSI Approved :: MIT License',
              'Topic :: Scientific/Engineering :: Astronomy',
              'Operating System :: POSIX',
              'Operating System :: Unix',
              'Operating System :: MacOS'],
          )
