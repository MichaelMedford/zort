#! /usr/bin/env python
"""
initialize.py
"""

import glob
import argparse
import pickle
import os
from tqdm import tqdm
from pathlib import Path
import sys

zortDir = '%s/zort' % Path(__file__).parent
sys.path.append(zortDir)
from parallel import parallel_process

dataDir = os.getenv('ZTF_OBJ_DATA')


def gather_lightcurve_files():
    fis = glob.glob('%s/field*.txt' % dataDir)
    return fis


def gather_source_files():
    fis = glob.glob('%s/field*.sources' % dataDir)
    return fis


def generate_sources_file(lightcurve_file):
    f_in = open(lightcurve_file, 'r')

    source_keys = ['id', 'nepochs', 'filterid',
                   'fieldid', 'rcid', 'ra', 'dec', 'buffer_position']

    sources_file = lightcurve_file.replace('.txt', '.sources')
    with open(sources_file, 'w') as f_out:
        f_out.write('%s\n' % ','.join(source_keys))

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

            buffer_position = f_in.tell() - len(line)
            f_out.write('%s,%i\n' % (data_str, buffer_position))

    f_in.close()


def generate_sources_files(parallelFlag=False, n_procs=1):
    lightcurve_files = gather_lightcurve_files()
    print('Genearting sources files for %i lightcurve files' % len(lightcurve_files))
    if parallelFlag:
        parallel_process(lightcurve_files, generate_sources_file, n_jobs=n_procs)
    else:
        for lightcurve_file in tqdm(lightcurve_files):
            generate_sources_file(lightcurve_file)


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


def generate_rcid_map(sources_file):
    f_in = open(sources_file, 'r')
    _ = f_in.readline()  # skip past the header

    rcid, rcid_current = None, None
    filterid, filterid_current = None, None
    buffer_location_start = None
    rcid_map = dict()
    rcid_map[1] = dict()
    rcid_map[2] = dict()

    while True:
        line = f_in.readline()
        buffer_location_current = f_in.tell() - len(line)

        # Check for end of the file
        if not line:
            rcid_map[filterid_current][rcid_current] = (
                buffer_location_start, buffer_location_current)
            break

        line_split = line.split(',')
        rcid = int(line_split[4])
        filterid = int(line_split[2])

        # Initialize the rcid
        if rcid_current is None:
            buffer_location_start = buffer_location_current
            rcid_current = rcid
            filterid_current = filterid

        # Check to see if the block has switched
        if rcid != rcid_current:
            rcid_map[filterid_current][rcid_current] = (
                buffer_location_start, buffer_location_current)
            buffer_location_start = buffer_location_current
            rcid_current = rcid
            filterid_current = filterid

    f_in.close()

    rcid_map_file = sources_file.replace('.sources', '.rcid_map')
    save_rcid_map(rcid_map_file, rcid_map)


def generate_rcid_maps(parallelFlag=False, n_procs=1):
    sources_files = gather_source_files()
    print('Genearting rcid maps for %i lightcurve files' % len(sources_files))
    if parallelFlag:
        parallel_process(sources_files, generate_rcid_map, n_jobs=n_procs)
    else:
        for sources_file in tqdm(sources_files):
            generate_rcid_map(sources_file)


def main():
    # Get arguments
    parser = argparse.ArgumentParser(description=__doc__)
    arguments = parser.add_argument_group('arguments')
    arguments.add_argument('--n_procs', type=int,
                           default=1,
                           help='Number of processors to assign to parallel tasks. '
                                'Default 1.')

    parallelgroup = parser.add_mutually_exclusive_group()
    parallelgroup.add_argument('--single', dest='parallelFlag',
                               action='store_false',
                               help='Run in single mode. DEFAULT.')
    parallelgroup.add_argument('--parallel', dest='parallelFlag',
                               action='store_true',
                               help='Run in parallel mode.')
    parser.set_defaults(parallelFlag=False)

    args = parser.parse_args()

    generate_sources_files(parallelFlag=args.parallelFlag, n_procs=args.n_procs)
    generate_rcid_maps(parallelFlag=args.parallelFlag, n_procs=args.n_procs)


if __name__ == '__main__':
    main()
