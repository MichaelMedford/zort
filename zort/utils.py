#! /usr/bin/env python
"""
utils.py
"""

import os

filterid_dict = {
    1: 'g',
    2: 'r',
    3: 'i'
}


def return_filename(filename):
    try:
        filename = filename.decode()
    except AttributeError:
        pass

    if filename is None:
        raise FileNotFoundError(filename)

    return filename


def return_objects_filename(filename):
    return _return_util_filename(filename, 'objects')


def return_objects_map_filename(filename):
    return _return_util_filename(filename, 'objects_map')


def return_radec_map_filename(filename):
    return _return_util_filename(filename, 'radec_map')


def return_rcid_map_filename(filename):
    return _return_util_filename(filename, 'rcid_map')


def _return_util_filename(filename, extension):
    util_filename = filename.replace('txt', extension)
    if os.path.exists(util_filename):
        return util_filename
    else:
        print('******')
        print('%s file missing, must be generated using '
              'zort-initialize to continue.' % extension)
        print("Run 'zort-initialize -h' or visit "
              "https://github.com/MichaelMedford/zort for more details.")
        print('******')
        raise FileNotFoundError(util_filename)
