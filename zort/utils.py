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
    objects_filename = filename.replace('.txt', '.objects')
    if os.path.exists(objects_filename):
        return objects_filename
    else:
        print('******')
        print('Objects file missing, must be generated using '
              'zort-initialize to continue.')
        print("Run 'zort-initialize -h' or visit "
              "https://github.com/MichaelMedford/zort for more details.")
        print('******')
        raise FileNotFoundError(objects_filename)


def return_rcid_map_filename(filename):
    rcid_map_filename = filename.replace('.txt', '.rcid_map')
    if os.path.exists(rcid_map_filename):
        return rcid_map_filename
    else:
        print('******')
        print('RCID map file missing, must be generated using '
              'zort-initialize to continue.')
        print("Run 'zort-initialize -h' or visit "
              "https://github.com/MichaelMedford/zort for more details.")
        print('******')
        raise FileNotFoundError(rcid_map_filename)
