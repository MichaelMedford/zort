#! /usr/bin/env python
"""
lightcurveFile.py
ZTF objects are stored in lightcurve files. This class allows for
iteration through a lightcurve file in order to inspect each object's
lightcurve. Filters can be applied to objects and/or lightcurves.
"""

import glob
import os
import pickle

from zort.object import Object
from zort.source import Source
from zort.utils import return_filename
from zort.utils import return_objects_filename, \
    return_radec_map_filename, \
    return_rcid_map_filename, \
    return_objects_map_filename
from zort.radec import return_rcid, return_shifted_ra


################################
#                              #
#  LightcurveFile Class        #
#                              #
################################

class LightcurveFile:
    """
    ZTF objects are stored in lightcurve files. This class allows for
    iteration through a lightcurve file in order to inspect each object's
    lightcurve. The user can select to start looping through the file at a
    specific object position.

    LightcurveFile should be used as an iterator to loop over all of the
    objects in the lightcurve file. Here is an example for how to
    (1) filter through the lightcurves in a lightcurve file and (2) recover
    the lightcurves of objects that pass a customized filter.

    The Object class (object.py) and the Lightcurve class (lightcurve.py) list
    out the attributes that can be run through the filter. These attributes
    include the object's number of epochs, filter, and sky location. Filters
    will almost certainly want to filter on the object's lightcurve, which
    contains the observation dates, magnitudes and magnitude errors.

    EXAMPLE 1:

    filename = 'field000000_lightcurve_file_example.txt'
    interesting_objects = []

    from zort.lightcurveFile import LightcurveFile
    for obj in LightcurveFile(filename):
        if my_interesting_filter(obj):
            interesting_objects.append(obj)

    from zort.object import save_objects
    save_objects('objects.list', interesting_objects)

    from zort.object import load_objects
    interesting_objects = load_objects('objects.list')
    for obj in interesting_objects:
        print(obj)
        print(obj.lightcurve)

    EXAMPLE 2:

    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size

    filename = 'field000000_lightcurve_file_example.txt'
    interesting_objects = []

    from zort.lightcurveFile import LightcurveFile
    for obj in LightcurveFile(filename, proc_rank=rank, proc_size=size):
        if my_interesting_filter(obj):
            interesting_objects.append(obj)

    from zort.object import save_objects
    save_objects('objects.%i.list' % rank, interesting_objects)
    """

    def __init__(self, filename,  proc_rank=0, proc_size=1,
                 apply_catmask=True, rcids_to_read=None):
        # Load filenames and check for existence
        self.filename = return_filename(filename)
        self.objects_filename = return_objects_filename(filename)
        self.objects_map_filename = return_objects_map_filename(filename)
        self.radec_map_filename = return_radec_map_filename(filename)
        self.rcid_map_filename = return_rcid_map_filename(filename)
        self.radec_map = self.load_radec_map()
        self.rcid_map = self.load_rcid_map()

        self.rcid_filters_to_read = self.load_rcid_filters_to_read(rcids_to_read)
        if len(self.rcid_filters_to_read) == 0:
            self.objects_file = self.return_objects_file()
            self.pointer_end = None
        else:
            filterid, rcid = self.rcid_filters_to_read.pop()
            pointer_start, pointer_end = self.rcid_map[filterid][rcid]
            self.objects_file = self.return_objects_file(pointer_start=pointer_start)
            self.pointer_end = self.rcid_map[filterid][rcid][1]

        self.objects_map = self.load_objects_map()

        self.proc_rank = proc_rank
        self.proc_size = proc_size
        self.fieldid = int(os.path.basename(filename).split('_')[0].
                           replace('field', ''))
        self.objects_counter = 0
        self.apply_catmask = apply_catmask

    def __iter__(self):
        return self

    def __next__(self):
        if self.pointer_end is None:
            raise StopIteration

        while self.objects_counter % self.proc_size != self.proc_rank:
            line = self._return_objects_file_line()
            if line is None:
                raise StopIteration

        line = self._return_objects_file_line()
        if line is None:
            raise StopIteration
        return self.return_object(line)

    def __exit__(self):
        self.objects_file.close()

    def _return_objects_file_line(self):
        line = self.objects_file.readline()
        pointer_current = self.objects_file.tell()

        if line == '' or pointer_current > self.pointer_end:
            if len(self.rcid_filters_to_read) == 0:
                return None
            filterid, rcid = self.rcid_filters_to_read.pop()
            pointer_start, pointer_end = self.rcid_map[filterid][rcid]
            self.pointer_end = pointer_end
            self.objects_file.seek(pointer_start)
            return self._return_objects_file_line()

        self.objects_counter += 1
        return line

    def _return_parsed_line(self, line):
        return line.replace('\n', '').split(',')

    def return_filename(self, filename):
        try:
            filename = filename.decode()
        except AttributeError:
            pass

        if filename is None:
            raise FileNotFoundError(filename)

        return filename

    def return_object(self, line):
        object_id = int(self._return_parsed_line(line)[0])
        return Object(self.filename,
                      object_id=object_id,
                      objects_map=self.objects_map,
                      radec_map=self.radec_map,
                      apply_catmask=self.apply_catmask)

    def return_objects_file(self, pointer_start=40):
        file = open(self.objects_filename, 'r')
        file.seek(pointer_start)
        return file

    def load_objects_map(self):
        objects_map = pickle.load(open(self.objects_map_filename, 'rb'))
        return objects_map

    def load_radec_map(self):
        radec_map = pickle.load(open(self.radec_map_filename, 'rb'))
        return radec_map
    
    def load_rcid_map(self):
        rcid_map = pickle.load(open(self.rcid_map_filename, 'rb'))
        return rcid_map

    def load_rcid_filters_to_read(self, rcids_to_read):
        if rcids_to_read is None:
            rcids_to_read = list(range(64))

        rcid_filters_to_read = []
        for filterid in [1, 2, 3]:
            if filterid not in self.rcid_map:
                continue
            for rcid in rcids_to_read:
                if rcid not in self.rcid_map[filterid]:
                    continue
                rcid_filters_to_read.append((filterid, rcid))

        return rcid_filters_to_read

    def locate_objects_by_radec(self, ra, dec, rcid=None, radius_as=2):
        if rcid is None:
            rcid = return_rcid(self.fieldid, ra, dec)
            if rcid is None:
                return

        radius_deg = radius_as / 3600.
        objects = []
        for filterid in self.radec_map:
            if rcid not in self.radec_map[filterid]:
                continue
            kdtree, lightcurve_position_arr = self.radec_map[filterid][rcid]
            ra_query = return_shifted_ra(ra, self.fieldid)
            idx_arr = kdtree.query_ball_point((ra_query, dec), radius_deg)
            if len(idx_arr) == 0:
                continue
            for idx in idx_arr:
                lightcurve_position = int(lightcurve_position_arr[idx])
                obj = Object(self.filename, lightcurve_position,
                             radec_map=self.radec_map, apply_catmask=self.apply_catmask)
                objects.append(obj)
        return objects

    def _extract_object_id_by_color(self, objects, color):
        objects_color = [obj for obj in objects if obj.color == color]
        if len(objects_color) == 0:
            return None
        elif len(objects_color) == 1:
            return objects_color[0].object_id
        else:
            print('Multiple objects found for filter %s. '
                  'Returning first.' % color)
            return objects_color[0].object_id

    def locate_source_by_radec(self, ra, dec, rcid=None, radius_as=2):
        objects = self.locate_objects_by_radec(ra, dec,
                                               rcid=rcid,
                                               radius_as=radius_as)
        if objects is None:
            return None
        g_object_id = self._extract_object_id_by_color(objects, 'g')
        r_object_id = self._extract_object_id_by_color(objects, 'r')
        i_object_id = self._extract_object_id_by_color(objects, 'i')
        if g_object_id is None and r_object_id is None and i_object_id is None:
            return None
        source = Source(self.filename,
                        object_id_g=g_object_id,
                        object_id_r=r_object_id,
                        object_id_i=i_object_id,
                        apply_catmask=self.apply_catmask,
                        radec_map=self.radec_map)
        return source


def _is_radec_in_lightcurveFile(filename, ra, dec):
    ra_bounds = filename.split('_')[1].replace('ra', '')
    ra_min = float(ra_bounds.split('to')[0])
    ra_max = float(ra_bounds.split('to')[1])

    if ra_max < ra_min:
        ra_max += 360
        if ra < 180:
            ra_query = ra + 360
        else:
            ra_query = ra
    else:
        ra_query = ra

    dec_bounds = filename.split('_')[2].replace('dec', '').replace('.txt', '')
    dec_min = float(dec_bounds.split('to')[0])
    dec_max = float(dec_bounds.split('to')[1])

    if ra_query < ra_min or ra_query > ra_max:
        return False
    if dec < dec_min or dec > dec_max:
        return False
    return True


def locate_objects_by_radec(ra, dec, radius_as=2):
    objects = []
    lightcurve_filenames = glob.glob('field*txt')
    for filename in lightcurve_filenames:
        if not _is_radec_in_lightcurveFile(filename, ra, dec):
            continue

        lightcurveFile = LightcurveFile(filename)
        objects_lightcurve = lightcurveFile.locate_objects_by_radec(ra, dec,
                                                                    radius_as=radius_as)
        if objects_lightcurve is not None:
            objects.extend(objects_lightcurve)

    return objects


def locate_sources_by_radec(ra, dec, radius_as=2):
    sources = []
    lightcurve_filenames = glob.glob('field*txt')
    for filename in lightcurve_filenames:
        if not _is_radec_in_lightcurveFile(filename, ra, dec):
            continue

        lightcurveFile = LightcurveFile(filename)
        source = lightcurveFile.locate_source_by_radec(ra, dec,
                                                       radius_as=radius_as)
        if source is not None:
            sources.append(source)

    return sources
