#! /usr/bin/env python
"""
__init__.py
"""

from pathlib import Path
import os
import sys
import glob

parentDir = Path(__file__).parent.parent
__version__ = open('%s/VERSION' % parentDir).readline().strip()

# The first time this script is called, you will be asked for the data directory of your ZTF lightcurves, as well
# as be forced into generating object files and rcid maps if they are not detected.

dataDir = os.getenv('ZTF_OBJ_DATA')
if dataDir is None:
    message = """
    Importing zort requires that all ZTF lightcurves in the Public Data Release(s) 
    are downloaded onto disk. zort looks for the location of those lightcurves
    at the environment variable ZTF_OBJ_DATA, which has not yet been set.

    Please input the location of the ZTF lightcurves. In the future you 
    will most likely want to set this location as an environment 
    variable ZTF_OBJ_DATA in your ~/.bashrc file or ~/.cshrc.

    Instructions for downloading and extracting these files for
    Data Release 1 can be found at: https://www.ztf.caltech.edu/page/dr1#12c
    
    Type 'exit' to cancel this import via SystemExit. 
    """
    print(message)
    dataDir = input()
    if dataDir == '':
        print('ZTF_OBJ_DATA not set. Exiting...')
        sys.exit()
    if dataDir == 'exit':
        print('Exiting...')
        sys.exit()
    print('ZTF_OBJ_DATA set to %s' % dataDir)

dataFiles = set(glob.glob('%s/field*txt' % dataDir))
objectFiles = set([f.replace('objects', 'txt') for f in glob.glob('%s/field*objects' % dataDir)])
if dataFiles != objectFiles:
    initializeFile = '%s/initialize.py' % parentDir
    message = f"""
    zort requires that all ZTF lightcurves on disk have a object file built 
    for faster data access. These object files do not appear to be in the 
    ZTF_OBJ_DATA folder.

    Object files must be generated from the lightcurve files currently 
    located in ZTF_OBJ_DATA. This process will take many hours with a 
    single processor and about one hour with 30 cores. 

    To generate object files either run:
    python {initializeFile}
    or
    python {initializeFile} --parallel --n-procs=$N_PROCS
    """
    print(message)
    sys.exit()
