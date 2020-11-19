#! /usr/bin/env python
"""
initialize.py
Initialization of object and rcip_map files.
"""


import os
import pickle
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree


def generate_objects_file(lightcurve_file):
    objects_file = lightcurve_file.replace('.txt', '.objects')
    if os.path.exists(objects_file):
        print('%s already exists. Skipping.' % objects_file)
        return

    f_in = open(lightcurve_file, 'r')

    object_keys = ['id', 'nepochs', 'filterid',
                   'fieldid', 'rcid', 'ra', 'dec', 'lightcurve_position']
    with open(objects_file, 'w') as f_out:
        f_out.write('%s\n' % ','.join(object_keys))

        while True:
            line = f_in.readline()

            # Check for end of the file
            if not line:
                break

            # Only want to look at object lines
            if not line.startswith('#'):
                continue

            data = line.replace('\n', '').split()[1:]
            data_str = ','.join(data)

            lightcurve_position = f_in.tell() - len(line)
            f_out.write('%s,%i\n' % (data_str, lightcurve_position))

    f_in.close()


def save_rcid_map(DR1_object_file, rcid_map):
    rcid_map_filename = DR1_object_file.replace('.objects', '.rcid_map')
    with open(rcid_map_filename, 'wb') as fileObj:
        pickle.dump(rcid_map, fileObj)


def return_rcid_map_size(rcid_map):
    rcid_map_size = 0
    for _, v in rcid_map.items():
        rcid_map_size += len(v)
    return rcid_map_size


def return_rcid_map_filesize(rcid_map):
    rcid_map_filesize = 0
    for k, _ in rcid_map.items():
        for _, t in rcid_map[k].items():
            rcid_map_filesize += t[1] - t[0]
    return rcid_map_filesize


def generate_rcid_map(lightcurve_file):
    rcid_map_file = lightcurve_file.replace('.txt', '.rcid_map')
    if os.path.exists(rcid_map_file):
        print('%s already exists. Skipping.' % rcid_map_file)
        return

    objects_file = lightcurve_file.replace('.txt', '.objects')

    f_in = open(objects_file, 'r')
    _ = f_in.readline()  # skip past the header

    rcid, rcid_current = None, None
    filterid, filterid_current = None, None
    ra_arr, dec_arr, lightcurve_position_arr = [], [], []
    rcid_map = defaultdict(dict)

    for line in f_in:
        data = line.replace('\n', '').split(',')

        rcid = int(data[4])
        filterid = int(data[2])

        # Initialize the rcid
        if rcid_current is None:
            rcid_current = rcid
            filterid_current = filterid

        # Check to see if the block has switched
        if rcid != rcid_current:
            objects = np.array([ra_arr, dec_arr]).T
            kdtree = cKDTree(objects)
            rcid_map[filterid_current][rcid_current] = \
                (kdtree, lightcurve_position_arr)

            rcid_current = rcid
            filterid_current = filterid
            ra_arr, dec_arr, lightcurve_position_arr = [], [], []

        ra, dec = float(data[5]), float(data[6])
        lightcurve_position = int(data[-1])
        ra_arr.append(ra)
        dec_arr.append(dec)
        lightcurve_position_arr.append(lightcurve_position)

    objects = np.array([ra_arr, dec_arr]).T
    kdtree = cKDTree(objects)
    rcid_map[filterid_current][rcid_current] = \
        (kdtree, lightcurve_position_arr)

    f_in.close()

    save_rcid_map(rcid_map_file, rcid_map)
