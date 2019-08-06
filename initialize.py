#! /usr/bin/env python
"""
initialize.py
"""

import glob
import random
from datetime import datetime
import argparse
import pickle
import os


def gather_DR1_field_files(parallelFlag=False):
    fis = glob.glob('field*.txt')
    fis = [f for f in fis if
           not os.path.exists(f.replace('.txt', '.objects_completed'))]
    random.shuffle(fis)

    if parallelFlag:
        fis.sort()

    return fis


def gather_DR1_object_files(parallelFlag=False):
    fis = glob.glob('field*.objects')
    fis = [f for f in fis if
           not os.path.exists(f.replace('.objects', '.rcid_map'))]
    random.shuffle(fis)

    if parallelFlag:
        fis.sort()

    return fis


def generate_object_file(DR1_file):
    fileObj = open(DR1_file, 'r')

    obj_keys = ['id', 'nepochs', 'filterid',
                'fieldid', 'rcid', 'ra', 'dec', 'buffer_position']

    object_file = DR1_file.replace('.txt', '.objects')
    with open(object_file, 'w') as f_out:
        f_out.write('%s\n' % ','.join(obj_keys))

        while True:
            line = fileObj.readline()

            # Check for end of the file
            if not line:
                break

            # Only want to look at object lines
            if not line.startswith('#'):
                continue

            data = line.replace('\n', '').split()[1:]
            data_str = ','.join(data)

            buffer_position = fileObj.tell() - len(line)
            f_out.write('%s,%i\n' % (data_str, buffer_position))

    fileObj.close()

    with open(object_file + '_completed', 'w') as f:
        f.write('')


def generate_object_files(parallelFlag=False):
    DR1_files = gather_DR1_field_files(parallelFlag=parallelFlag)

    if parallelFlag:
        from mpi4py import MPI
        comm = MPI.COMM_WORLD
        rank = comm.rank
        size = comm.size

        my_DR1_files = []
        idx = rank
        while idx < len(DR1_files):
            my_DR1_files.append(DR1_files[idx])
            idx += size
    else:
        rank = 0
        my_DR1_files = DR1_files

    for i, DR1_file in enumerate(my_DR1_files):
        now = datetime.now()
        print('%i) Generating object_files for %s (%i/%i) | %s' % (
            rank, DR1_file, i, len(my_DR1_files),
            now.strftime("%m/%d/%Y, %H:%M:%S")))
        generate_object_file(DR1_file)


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


def generate_rcid_map(DR1_object_file):
    fileObj = open(DR1_object_file, 'r')
    _ = fileObj.readline()  # skip past the header

    rcid, rcid_current = None, None
    filterid, filterid_current = None, None
    buffer_location_start = None
    rcid_map = dict()
    rcid_map[1] = dict()
    rcid_map[2] = dict()

    while True:
        line = fileObj.readline()
        buffer_location_current = fileObj.tell() - len(line)

        # Check for end of the file
        if not line:
            rcid_map[filterid_current][rcid_current] = (
                buffer_location_start, buffer_location_current)
            # print(return_rcid_map_size(rcid_map))
            break

        line_split = line.split(',')
        rcid = int(line_split[4])
        filterid = int(line_split[2])

        # Initialize the rcid
        if rcid_current is None:
            # print(return_rcid_map_size(rcid_map))
            buffer_location_start = buffer_location_current
            rcid_current = rcid
            filterid_current = filterid

        # Check to see if the block has switched
        if rcid != rcid_current:
            rcid_map[filterid_current][rcid_current] = (
                buffer_location_start, buffer_location_current)
            # print(return_rcid_map_size(rcid_map))
            buffer_location_start = buffer_location_current
            rcid_current = rcid
            filterid_current = filterid

    fileObj.close()

    return rcid_map


def generate_rcid_maps(parallelFlag=False):
    DR1_object_files = gather_DR1_object_files(parallelFlag=parallelFlag)

    if parallelFlag:
        from mpi4py import MPI
        comm = MPI.COMM_WORLD
        rank = comm.rank
        size = comm.size

        my_DR1_object_files = []
        idx = rank
        while idx < len(DR1_object_files):
            my_DR1_object_files.append(DR1_object_files[idx])
            idx += size
    else:
        rank = 0
        my_DR1_object_files = DR1_object_files

    for i, DR1_object_file in enumerate(my_DR1_object_files):
        now = datetime.now()
        print('%i) Generating rcid_map for %s (%i/%i) | %s' % (
            rank, DR1_object_file, i, len(my_DR1_object_files),
            now.strftime("%m/%d/%Y, %H:%M:%S")))
        rcid_map = generate_rcid_map(DR1_object_file)
        save_rcid_map(DR1_object_file, rcid_map)


def main():
    # Get arguments
    parser = argparse.ArgumentParser(description=__doc__)

    parallelgroup = parser.add_mutually_exclusive_group()
    parallelgroup.add_argument('--single', dest='parallelFlag',
                               action='store_false',
                               help='Run in single mode. DEFAULT.')
    parallelgroup.add_argument('--parallel', dest='parallelFlag',
                               action='store_true',
                               help='Run in parallel mode.')
    parser.set_defaults(parallelFlag=False)

    args = parser.parse_args()

    generate_object_files(parallelFlag=args.parallelFlag)
    generate_rcid_maps(parallelFlag=args.parallelFlag)


if __name__ == '__main__':
    main()
