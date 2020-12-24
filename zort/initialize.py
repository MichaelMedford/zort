#! /usr/bin/env python
"""
initialize.py
Initialization of object, object_map and radec_map files.
"""


import os
import pickle
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree
from zort.radec import lightcurve_file_is_pole


def generate_objects_file(lightcurve_file):
    objects_file = lightcurve_file.replace('.txt', '.objects')
    if os.path.exists(objects_file):
        print('%s already exists. Skipping.' % objects_file)
        return

    f_in = open(lightcurve_file, 'r')
    object_map = {}
    object_keys = ['id', 'nepochs', 'filterid',
                   'fieldid', 'rcid', 'ra', 'dec']
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
            f_out.write('%s\n' % data_str)

            object_id = int(data_str.split(',')[0])
            lightcurve_position = f_in.tell() - len(line)
            object_map[object_id] = lightcurve_position

    f_in.close()

    objects_file = lightcurve_file.replace('.txt', '.objects_map')
    with open(objects_file, 'wb') as fileObj:
        pickle.dump(object_map, fileObj)


def save_radec_map(lightcurve_file, radec_map):
    _save_map(lightcurve_file, radec_map, 'radec_map')
    
    
def save_rcid_map(lightcurve_file, rcid_map):
    _save_map(lightcurve_file, rcid_map, 'rcid_map')


def _save_map(lightcurve_file, map, extension):
    map_filename = lightcurve_file.replace('txt', extension)
    with open(map_filename, 'wb') as fileObj:
        pickle.dump(map, fileObj)


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


def generate_radec_rcid_maps(lightcurve_file):
    radec_map_file = lightcurve_file.replace('.txt', '.radec_map')
    if os.path.exists(radec_map_file):
        print('%s already exists. Skipping.' % radec_map_file)
        return

    rcid_map_file = lightcurve_file.replace('.txt', '.rcid_map')
    if os.path.exists(rcid_map_file):
        print('%s already exists. Skipping.' % rcid_map_file)
        return

    objects_file = lightcurve_file.replace('.txt', '.objects')

    f_in = open(objects_file, 'r')
    _ = f_in.readline()  # skip past the header

    rcid, rcid_current = None, None
    filterid, filterid_current = None, None
    ra_arr, dec_arr, object_id_arr = [], [], []
    radec_map = defaultdict(dict)
    object_location_start = None
    rcid_map = defaultdict(dict)

    is_pole = lightcurve_file_is_pole(lightcurve_file)

    while True:
        line = f_in.readline()
        object_location_current = f_in.tell() - len(line)

        # Check for end of the file
        if not line:
            break

        data = line.replace('\n', '').split(',')

        object_id = int(data[0])
        rcid = int(data[4])
        filterid = int(data[2])

        # Initialize the rcid
        if rcid_current is None:
            object_location_start = object_location_current
            rcid_current = rcid
            filterid_current = filterid

        # Check to see if the block has switched
        if rcid != rcid_current:
            # set bounds of rcid
            rcid_map[filterid_current][rcid_current] = (
                object_location_start, object_location_current)
            object_location_start = object_location_current

            # build kdtree for rcid
            objects = np.array([ra_arr, dec_arr]).T
            kdtree = cKDTree(objects)
            radec_map[filterid_current][rcid_current] = \
                (kdtree, object_id_arr)

            # update rcid and filter for new region
            rcid_current = rcid
            filterid_current = filterid
            ra_arr, dec_arr, object_id_arr = [], [], []

        ra, dec = float(data[5]), float(data[6])
        if is_pole and ra > 180:
            ra -= 360

        ra_arr.append(ra)
        dec_arr.append(dec)
        object_id_arr.append(object_id)

    # update rcid_map with final rcid
    rcid_map[filterid_current][rcid_current] = (
        object_location_start, object_location_current)

    # build kdtree for final rcid
    objects = np.array([ra_arr, dec_arr]).T
    kdtree = cKDTree(objects)
    radec_map[filterid_current][rcid_current] = \
        (kdtree, object_id_arr)

    f_in.close()

    save_radec_map(lightcurve_file, radec_map)
    save_rcid_map(lightcurve_file, rcid_map)
