#! /usr/bin/env python
"""
source.py
A source contains one or more Objects that are spatially coincident, each
containing a single color lightcurve of a ZTF object.
"""
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from zort.lightcurve import Lightcurve
from zort.utils import return_filename, return_objects_filename, \
    return_radec_map_filename, filterid_dict


################################
#                              #
#  Source Class                #
#                              #
################################

class Source:
    """
    A source contains one or more Objects that are spatially coincident, each
    containing a single color lightcurve of a ZTF object. All objects within
    source must be from the same lightcurve file.
    """

    def __init__(self, filename, lightcurve_position_g=None,
                 lightcurve_position_r=None, lightcurve_position_i=None,
                 apply_catmask=False, PS_g_minus_r=0, radec_map=None):
        # Load filenames and check for existence
        self.filename = return_filename(filename)
        self.objects_filename = return_objects_filename(filename)
        self.radec_map_filename = return_radec_map_filename(filename)

        self.lightcurve_position_g = lightcurve_position_g
        self.lightcurve_position_r = lightcurve_position_r
        self.lightcurve_position_i = lightcurve_position_i
        self._check_lightcurve_positions()

        self.apply_catmask = apply_catmask
        self.PS_g_minus_r = PS_g_minus_r
        if radec_map:
            self.radec_map = radec_map
        else:
            self.radec_map = None

        self._load_objects()

    def __repr__(self):
        title = 'Filename: %s\n' % self.filename.split('/')[-1]
        title += 'Lightcurve Buffer Position: %i\n' % self.lightcurve_position
        title += 'Object ID: %i\n' % self.objectid
        title += 'Filter ID: %i | Color: %s\n' % (self.filterid, self.color)
        title += 'Ra/Dec: (%.5f, %.5f)\n' % (self.ra, self.dec)
        if self.apply_catmask:
            title += '%i Epochs passing catmask\n' % self.lightcurve.nepochs
        else:
            title += '%i Epochs without applying catmask\n' % self.lightcurve.nepochs
        title += '%i siblings identified\n' % len(self.siblings)

        return title

    def _check_lightcurve_positions(self):
        if self.lightcurve_position_g is None \
                and self.lightcurve_position_r is None \
                and self.lightcurve_position_i is None:
            raise Exception('Source must be instantiated '
                            'with at least one lightcurve position')

    def _load_objects(self):



    def load_radec_map(self):
        radec_map_filename = self.radec_map_filename
        radec_map = pickle.load(open(radec_map_filename, 'rb'))
        return radec_map


def save_objects(filename, objects, overwrite=False):
    if os.path.exists(filename) and not overwrite:
        print('%s already exists, exiting without saving objects. '
              'Set overwrite=True to enable writing over existing '
              'object lists.' % filename)
        return None

    with open(filename, 'w') as f:
        for obj in objects:
            f.write('%s,%i\n' % (obj.filename, obj.lightcurve_position))


def load_objects(filename):
    objects = []
    for line in open(filename, 'r'):
        filename, lightcurve_position = line.replace('\n', '').split(',')
        objects.append(Object(filename, lightcurve_position))

    return objects
