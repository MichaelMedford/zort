#! /usr/bin/env python
"""
source.py
A source contains one or more Objects that are spatially coincident, each
containing a single color lightcurve of a ZTF object.
"""
import os
import pickle
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

from zort.lightcurve import Lightcurve
from zort.object import Object
from zort.plot import plot_objects
from zort.utils import return_filename, return_objects_map_filename, \
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
    source must be from the same lightcurve file.d
    """

    def __init__(self, filename, object_id_g=None,
                 object_id_r=None, object_id_i=None,
                 lightcurve_position_g=None,
                 lightcurve_position_r=None,
                 lightcurve_position_i=None,
                 apply_catmask=False, PS_g_minus_r=0,
                 objects_map=None,
                 radec_map=None):
        # Load filenames and check for existence
        self.filename = return_filename(filename)
        self.objects_map_filename = return_objects_map_filename(filename)
        self.radec_map_filename = return_radec_map_filename(filename)

        self._check_initialization(object_id_g, object_id_r, object_id_i,
                                   lightcurve_position_g,
                                   lightcurve_position_r,
                                   lightcurve_position_i)

        self.apply_catmask = apply_catmask
        self.PS_g_minus_r = PS_g_minus_r
        if objects_map:
            self.objects_map = objects_map
        else:
            self.objects_map = None
        if radec_map:
            self.radec_map = radec_map
        else:
            self.radec_map = None

        objects = self._load_objects(object_id_g, object_id_r, object_id_i,
                                     lightcurve_position_g,
                                     lightcurve_position_r,
                                     lightcurve_position_i)
        self.object_g = objects[0]
        self.object_r = objects[1]
        self.object_i = objects[2]
        self.objects = [o for o in objects if o is not None]

        radec = self._calculate_radec()
        self.ra = radec[0]
        self.dec = radec[1]

        self._glonlat = None

    @property
    def glonlat(self):
        if self._glonlat is None:
            coord = SkyCoord(self.ra, self.dec, unit=u.degree, frame='icrs')
            glon, glat = coord.galactic.l.value, coord.galactic.b.value
            if glon > 180:
                glon -= 360
            self._glonlat = (glon, glat)
        return self._glonlat

    @property
    def glon(self):
        return self.glonlat[0]

    @property
    def glat(self):
        return self.glonlat[1]

    def _return_object_print_info(self, object):
        if object is None:
            object_id, nepochs = None, None
        else:
            object_id, nepochs = object.object_id, object.nepochs
        return {'id': object_id, 'nepochs': nepochs}

    def __repr__(self):
        title = 'Filename: %s\n' % self.filename.split('/')[-1]
        title += 'Object-g ID: {id} | nepochs: {nepochs}\n'.format(
            **self._return_object_print_info(self.object_g))
        title += 'Object-r ID: {id} | nepochs: {nepochs}\n'.format(
            **self._return_object_print_info(self.object_r))
        title += 'Object-i ID: {id} | nepochs: {nepochs}\n'.format(
            **self._return_object_print_info(self.object_i))
        title += 'Ra/Dec: (%.5f, %.5f)\n' % (self.ra, self.dec)

        return title

    def _check_initialization(self,
                              object_id_g, object_id_r, object_id_i,
                              lightcurve_position_g,
                              lightcurve_position_r,
                              lightcurve_position_i):
        arr = np.array([object_id_g, object_id_r, object_id_i,
                        lightcurve_position_g, lightcurve_position_r,
                        lightcurve_position_i])
        if np.all(arr == None):
            raise Exception('Source must be instantiated '
                            'with at least one Object ID '
                            'or lightcurve position.')

        if object_id_g is not None and lightcurve_position_g is not None:
            raise Exception('Only initialize g object with Object ID '
                            'or lightcurve position, but not both.')

        if object_id_r is not None and lightcurve_position_r is not None:
            raise Exception('Only initialize r object with Object ID '
                            'or lightcurve position, but not both.')

        if object_id_i is not None and lightcurve_position_i is not None:
            raise Exception('Only initialize i object with Object ID '
                            'or lightcurve position, but not both.')

    def _load_object(self, object_id, lightcurve_position, color):
        if object_id is None and lightcurve_position is None:
            return None

        if lightcurve_position is not None:
            obj = Object(self.filename,
                         lightcurve_position=lightcurve_position,
                         objects_map=self.objects_map)
        else:
            if self.objects_map is None:
                self.objects_map = self.load_objects_map()
            obj = Object(self.filename,
                         object_id=object_id,
                         objects_map=self.objects_map)
        if obj.color != color:
            str = "Color of 'object_id_{color}' is {color_obj}. " \
                  "Must be {color}.".format(color=color,
                                            color_obj=obj.color)
            raise Exception(str)
        return obj

    def _load_objects(self, object_id_g, object_id_r, object_id_i,
                      lightcurve_position_g, lightcurve_position_r, lightcurve_position_i):
        object_g = self._load_object(object_id=object_id_g,
                                     lightcurve_position=lightcurve_position_g,
                                     color='g')
        object_r = self._load_object(object_id=object_id_r,
                                     lightcurve_position=lightcurve_position_r,
                                     color='r')
        object_i = self._load_object(object_id=object_id_i,
                                     lightcurve_position=lightcurve_position_i,
                                     color='i')
        return object_g, object_r, object_i

    def _calculate_radec(self):
        ra = np.mean([obj.ra for obj in self.objects if obj is not None])
        dec = np.mean([obj.dec for obj in self.objects if obj is not None])
        return ra, dec

    def load_objects_map(self):
        objects_map_filename = self.objects_map_filename
        objects_map = pickle.load(open(objects_map_filename, 'rb'))
        return objects_map

    def load_radec_map(self):
        radec_map_filename = self.radec_map_filename
        radec_map = pickle.load(open(radec_map_filename, 'rb'))
        return radec_map

    def plot_lightcurves(self, filename=None, insert_radius=30):
        if filename is None:
            object_ids = '_'.join([str(obj.object_id) for obj in self.objects
                                   if obj is not None])
            filename = '%s_%s.png' % (self.filename.replace('.txt', ''),
                                      object_ids)

        plot_objects(filename=filename,
                     object_g=self.object_g,
                     object_r=self.object_r,
                     object_i=self.object_i,
                     insert_radius=insert_radius)


def create_source_from_object(object, locate_siblings=True, radius_as=2, skip_filterids=None):
    if locate_siblings and object.siblings is None:
        object.locate_siblings(radius_as=radius_as,
                               skip_filterids=skip_filterids)
    source_dict = {'g': None, 'r': None, 'i': None,
                   object.color: object.object_id}
    for sibling in object.siblings:
        source_dict[sibling.color] = sibling.object_id

    return Source(filename=object.filename,
                  object_id_g=source_dict['g'],
                  object_id_r=source_dict['r'],
                  object_id_i=source_dict['i'])


def save_sources(filename, sources, overwrite=False):
    if os.path.exists(filename) and not overwrite:
        print('%s already exists, exiting without saving objects. '
              'Set overwrite=True to enable writing over existing '
              'object lists.' % filename)
        return None

    with open(filename, 'w') as f:
        for source in sources:
            f.write('%s,%s,%s,%s\n' % (source.filename,
                                       source.object_id_g,
                                       source.object_id_r,
                                       source.object_id_i))


def load_sources(filename):
    sources = []
    for line in open(filename, 'r'):
        filename, object_id_g, object_id_r, object_id_i = line.replace('\n', '').split(',')
        sources.append(Source(filename,
                              object_id_g=object_id_g,
                              object_id_r=object_id_r,
                              object_id_i=object_id_i))

    return sources
