#! /usr/bin/env python
"""
initialize.py
Initialization of object, object_map and r_map files.
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
    object_map = {}
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

            object_id = int(data_str.split(',')[0])
            object_map[object_id] = lightcurve_position

    f_in.close()

    objects_file = lightcurve_file.replace('.txt', '.objects_map')
    with open(objects_file, 'wb') as fileObj:
        pickle.dump(object_map, fileObj)


def save_radec_map(DR1_object_file, radec_map):
    radec_map_filename = DR1_object_file.replace('.objects', '.radec_map')
    with open(radec_map_filename, 'wb') as fileObj:
        pickle.dump(radec_map, fileObj)


def return_radec_map_size(radec_map):
    radec_map_size = 0
    for _, v in radec_map.items():
        radec_map_size += len(v)
    return radec_map_size


def return_radec_map_filesize(radec_map):
    radec_map_filesize = 0
    for k, _ in radec_map.items():
        for _, t in radec_map[k].items():
            radec_map_filesize += t[1] - t[0]
    return radec_map_filesize


def generate_radec_map(lightcurve_file):
    radec_map_file = lightcurve_file.replace('.txt', '.radec_map')
    if os.path.exists(radec_map_file):
        print('%s already exists. Skipping.' % radec_map_file)
        return

    objects_file = lightcurve_file.replace('.txt', '.objects')

    f_in = open(objects_file, 'r')
    _ = f_in.readline()  # skip past the header

    rcid, rcid_current = None, None
    filterid, filterid_current = None, None
    ra_arr, dec_arr, lightcurve_position_arr = [], [], []
    radec_map = defaultdict(dict)

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
            radec_map[filterid_current][rcid_current] = \
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
    radec_map[filterid_current][rcid_current] = \
        (kdtree, lightcurve_position_arr)

    f_in.close()

    save_radec_map(radec_map_file, radec_map)
