#! /usr/bin/env python
"""
initialize.py
Initialization of object and rcip_map files.
"""


import glob
import os
import pickle
from collections import defaultdict


def gather_lightcurve_files(dataDir):
    fis = [f for f in glob.glob('%s/field*.txt' % dataDir) if
           not os.path.exists(f.replace('.txt', '.rcid_map'))]
    fis.sort()
    return fis


def generate_objects_file(lightcurve_file):
    f_in = open(lightcurve_file, 'r')

    object_keys = ['id', 'nepochs', 'filterid',
                   'fieldid', 'rcid', 'ra', 'dec', 'lightcurve_position']

    objects_file = lightcurve_file.replace('.txt', '.objects')
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
    objects_file = lightcurve_file.replace('.txt', '.objects')

    f_in = open(objects_file, 'r')
    _ = f_in.readline()  # skip past the header

    rcid, rcid_current = None, None
    filterid, filterid_current = None, None
    object_location_start = None
    rcid_map = defaultdict(dict)

    while True:
        line = f_in.readline()
        object_location_current = f_in.tell() - len(line)

        # Check for end of the file
        if not line:
            rcid_map[filterid_current][rcid_current] = (
                object_location_start, object_location_current)
            break

        line_split = line.split(',')
        rcid = int(line_split[4])
        filterid = int(line_split[2])

        # Initialize the rcid
        if rcid_current is None:
            object_location_start = object_location_current
            rcid_current = rcid
            filterid_current = filterid

        # Check to see if the block has switched
        if rcid != rcid_current:
            rcid_map[filterid_current][rcid_current] = (
                object_location_start, object_location_current)
            object_location_start = object_location_current
            rcid_current = rcid
            filterid_current = filterid

    f_in.close()

    rcid_map_file = objects_file.replace('.objects', '.rcid_map')
    save_rcid_map(rcid_map_file, rcid_map)
