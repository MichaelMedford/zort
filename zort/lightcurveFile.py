#! /usr/bin/env python
"""
lightcurveFile.py
ZTF objects are stored in lightcurve files. This class allows for
iteration through a lightcurve file in order to inspect each object's
lightcurve. Filters can be applied to objects and/or lightcurves.
"""

import os
import pickle
from zort.object import Object


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
    specific buffer position.

    LightcurveFile should be used as an iterator to loop over all of the
    objects in the lightcurve file. Here is an example for how to
    (1) filter through the lightcurves in a lightcurve file and (2) recover
    the lightcurves of objects that pass a customized filter.

    The Object class (object.py) and the Lightcurve class (lightcurve.py) list
    out the attributes that can be run through the filter. These attributes
    include the object's number of epochs, filter, and sky location. Filters
    will almost certainly want to filter ont he object's lightcurve, which
    contains the observations dates, magnitudes and magnitude errors.

    EXAMPLE:

    filename = 'field000245_ra357.03053to5.26702_dec-27.96964to-20.4773.txt'

    from zort.lightcurveFile import LightcurveFile
    interesting_objects = []
    for obj in LightcurveFile(filename, nepochs_cut=10):
        if my_interesting_filter(obj):
            interesting_objects.append(obj.buffer_position)

    from zort.object import Object
    for buffer_position in interesting_objects:
        obj = Object(filename, buffer_position)
        print(obj)
        print(obj.lightcurve)
    """

    def __init__(self, filename, init_buffer_position=56):
        self.filename = self._set_filename(filename)
        self.objects_filename = self.return_objects_filename()
        self.init_buffer_position = init_buffer_position
        self.objects_file = self.return_objects_file()
        self.rcid_map = self.load_rcid_map()

    def __iter__(self):
        return self

    def __next__(self):
        line = self.objects_file.readline()
        if line == '':
            raise StopIteration
        else:
            return self.return_object(line)

    def __exit__(self):
        self.objects_file.close()

    def _return_parsed_line(self, line):
        return line.replace('\n', '').split(',')

    def _set_filename(self, filename):
        try:
            filename = filename.decode()
        except AttributeError:
            pass

        return filename

    def return_object(self, line):
        buffer_position = self._return_parsed_line(line)[-1]
        return Object(self.filename, buffer_position)

    def return_objects_file(self):
        # Attempt to open file containing the lightcurve
        try:
            file = open(self.objects_filename, 'r')
        except FileNotFoundError as e:
            print(e)
            return None
        file.seek(self.init_buffer_position)
        return file

    def return_objects_filename(self):
        objects_filename = self.filename.replace('.txt', '.objects')
        return objects_filename

    def load_rcid_map(self):
        # Attempt to locate the rcid map for this object's file
        rcid_map_filename = self.filename.replace('.txt', '.rcid_map')
        if not os.path.exists(rcid_map_filename):
            print('** rcid_map missing! **')
            return None

        rcid_map = pickle.load(open(rcid_map_filename, 'rb'))
        return rcid_map

    def locate_objects_by_radec(self, ra, dec, rcid, radius=3.):
        objects = []
        for fid in [1, 2]:
            buffer_start, buffer_end = self.rcid_map[fid][rcid]
            self.objects_file.seek(buffer_start)
            buffer_location = self.objects_file.tell()
            while buffer_location < buffer_end:
                line = self.objects_file.readline()
                if line == '':
                    break
                else:
                    object = self.return_object(line)
                    object.sibling_tol_as = radius
                    if object.test_radec(ra, dec):
                        objects.append(object)
                buffer_location = self.objects_file.tell()
        return objects
