#! /usr/bin/env python
"""
lightcurveFile.py
ZTF objects are stored in lightcurve files. This class allows for
iteration through a lightcurve file in order to inspect each object's
lightcurve. Filters can be applied to objects and/or lightcurves.
"""

import pickle
from zort.object import Object
from zort.utils import return_filename
from zort.utils import return_objects_filename
from zort.utils import return_rcid_map_filename


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

    from zort.objcet import save_obejcts
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

    def __init__(self, filename, init_object_position=60,
                 proc_rank=0, proc_size=1, apply_catmask=True):
        # Load filenames and check for existence
        self.filename = return_filename(filename)
        self.objects_filename = return_objects_filename(filename)
        self.rcid_map_filename = return_rcid_map_filename(filename)

        self.init_object_position = init_object_position
        self.objects_file = self.return_objects_file()
        self.rcid_map = self.load_rcid_map()
        self.proc_rank = proc_rank
        self.proc_size = proc_size
        self.objects_file_counter = 0
        self.apply_catmask = apply_catmask

    def __iter__(self):
        return self

    def __next__(self):
        while self.objects_file_counter % self.proc_size != self.proc_rank:
            line = self._return_objects_file_line()
            if line == '':
                raise StopIteration

        line = self._return_objects_file_line()
        if line == '':
            raise StopIteration
        return self.return_object(line)

    def __exit__(self):
        self.objects_file.close()

    def _return_objects_file_line(self):
        line = self.objects_file.readline()
        self.objects_file_counter += 1
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
        lightcurve_position = self._return_parsed_line(line)[-1]
        return Object(self.filename, lightcurve_position,
                      apply_catmask=self.apply_catmask)

    def return_objects_file(self):
        file = open(self.objects_filename, 'r')
        file.seek(self.init_object_position)
        return file

    def load_rcid_map(self):
        rcid_map = pickle.load(open(self.rcid_map_filename, 'rb'))
        return rcid_map

    def locate_objects_by_radec(self, ra, dec, rcid, radius=3.):
        objects = []
        for fid in [1, 2]:
            location_start, location_end = self.rcid_map[fid][rcid]
            self.objects_file.seek(location_start)
            object_location = self.objects_file.tell()
            while object_location < location_end:
                line = self.objects_file.readline()
                if line == '':
                    break
                else:
                    object = self.return_object(line)
                    object.sibling_tol_as = radius
                    if object.test_radec(ra, dec):
                        objects.append(object)
                object_location = self.objects_file.tell()
        return objects
