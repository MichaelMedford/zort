#! /usr/bin/env python
"""
__init__.py
"""

from pathlib import Path

parentDir = Path(__file__).parent.parent
__version__ = open('%s/VERSION' % parentDir).readline().strip()

# The first time this script is called, you will be asked for the data directory of your ZTF lightcurves, as well
# as the opportunity to build (or download) object files and rcid_map files if they are not detected.
