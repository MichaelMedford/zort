#! /usr/bin/env python
"""
object.py
Each ZTF object can be represented as an instance of the Object class, along
with its metadata and lightcurve. Note that each ZTF object is only one color,
with a different color of the same astrophysical object labelled as a different
object. This class can find and save spatially coincident objects with the
locate_siblings function.
"""
import os
import pickle
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

from zort.lightcurve import Lightcurve
from zort.utils import return_filename, return_objects_filename, \
    return_objects_map_filename, return_radec_map_filename, \
    filterid_dict
from zort.plot import plot_object, plot_objects
from zort.radec import field_is_pole


################################
#                              #
#  Object Class                #
#                              #
################################

class Object:
    """
    Each ZTF object can be represented as an instance of the Object class,
    along with its parameters and lightcurve. Note that each ZTF object is only
    one color, with a different color from the same astrophysical source
    labelled as a different object. This class can find and save spatially
    coincident objects with the locate_siblings function.
    """

    def __init__(self, filename, object_id=None, lightcurve_position=None,
                 apply_catmask=False, PS_g_minus_r=0,
                 objects_map=None, radec_map=None):
        # Check object_id and lightcurve_position
        if object_id is None and lightcurve_position is None:
            raise Exception('ObjectID or lightcurve_position must be defined.')
        elif object_id is not None and lightcurve_position is not None:
            raise Exception('Only initialize object with Object ID '
                            'or lightcurve position, but not both.')

        # Load filenames and check for existence
        self.filename = return_filename(filename)
        self.objects_filename = return_objects_filename(filename)
        self.objects_map_filename = return_objects_map_filename(filename)
        self.radec_map_filename = return_radec_map_filename(filename)

        self.objects_map = None
        if object_id is not None:
            if objects_map:
                self.objects_map = objects_map
            else:
                self.objects_map = self.load_objects_map()
            self.lightcurve_position = self.objects_map[object_id]
        elif lightcurve_position is not None:
            self.lightcurve_position = lightcurve_position

        params = self._load_params()
        self.object_id = params['object_id']
        self.nepochs = params['nepochs']
        self.filterid = params['filterid']
        self.fieldid = params['fieldid']
        self.rcid = params['rcid']
        self.ra = params['ra']
        self.dec = params['dec']
        self.color = self._return_filterid_color()
        self.apply_catmask = apply_catmask
        self.PS_g_minus_r = PS_g_minus_r
        self._lightcurve = None
        self.siblings = None
        self.nsiblings = 0
        self._glonlat = None

        if radec_map:
            self.radec_map = radec_map
        else:
            self.radec_map = None

    def __repr__(self):
        title = 'Filename: %s\n' % self.filename.split('/')[-1]
        title += 'Object ID: %i\n' % self.object_id
        title += 'Filter ID: %i | Color: %s\n' % (self.filterid, self.color)
        title += 'Ra/Dec: (%.5f, %.5f)\n' % (self.ra, self.dec)
        if self.apply_catmask:
            title += '%i Epochs passing catmask\n' % self.lightcurve.nepochs
        else:
            title += '%i Epochs without applying catmask\n' % self.lightcurve.nepochs
        title += '%i siblings identified\n' % self.nsiblings
        title += 'Lightcurve Buffer Position: %i\n' % self.lightcurve_position

        return title

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

    def _load_params(self):
        # Open lightcurve file
        file = open(self.filename, 'r')

        # Jump to the location of the object in the lightcurve file
        file.seek(self.lightcurve_position)

        line = file.readline()
        params = line.split()[1:]

        params_dict = dict()
        params_dict['object_id'] = int(params[0])
        params_dict['nepochs'] = int(params[1])
        params_dict['filterid'] = int(params[2])
        params_dict['fieldid'] = int(params[3])
        params_dict['rcid'] = int(params[4])
        params_dict['ra'] = float(params[5])
        params_dict['dec'] = float(params[6])
        return params_dict

    def _return_filterid_color(self):
        # Defined by ZTF convention
        return filterid_dict[self.filterid]

    def load_objects_map(self):
        objects_map_filename = self.objects_map_filename
        objects_map = pickle.load(open(objects_map_filename, 'rb'))
        return objects_map

    def load_radec_map(self):
        radec_map_filename = self.radec_map_filename
        radec_map = pickle.load(open(radec_map_filename, 'rb'))
        return radec_map

    def return_siblings_filename(self):
        siblings_filename = self.filename.replace('.txt', '.siblings')
        return siblings_filename

    @property
    def lightcurve(self):
        if not self._lightcurve:
            self._lightcurve = self._load_lightcurve()
        return self._lightcurve

    def _load_lightcurve(self):
        return Lightcurve(self.filename, self.lightcurve_position,
                          apply_catmask=self.apply_catmask,
                          PS_g_minus_r=self.PS_g_minus_r)

    def set_siblings(self, sibling_object_ids, printFlag=False):
        # Assign the sibling to its own object instance
        siblings = []
        for object_id in sibling_object_ids:
            sib = Object(self.filename, object_id,
                         objects_map=self.objects_map,
                         radec_map=self.radec_map)
            siblings.append(sib)
            if printFlag:
                print('---- Sibling found at %.5f, %.5f !' % (
                    sib.ra, sib.dec))
                print('---- Original Color: %s | Sibling Color: %s' % (
                    self.color, sib.color))
        self.siblings = siblings
        self.nsiblings = len(siblings)

    def locate_siblings(self, radius_as=2,
                        skip_filterids=None, printFlag=False):
        radius_deg = radius_as / 3600.
        if printFlag:
            print('Locating siblings for ZTF Object %i' % self.object_id)
            print('-- Object location: %.5f, %.5f ...' % (self.ra, self.dec))

        if self.radec_map is None:
            self.radec_map = self.load_radec_map()

        # Searching for siblings in the opposite
        # filtered sections of the radec_map
        sibling_filterids = [i for i in [1, 2, 3] if i != self.filterid]
        if skip_filterids:
            sibling_filterids = [i for i in sibling_filterids
                                 if i not in skip_filterids]
        rcid = self.rcid
        siblings_object_ids = []
        is_pole = field_is_pole(self.fieldid)

        for filterid in sibling_filterids:
            color = filterid_dict[filterid]
            if filterid not in self.radec_map:
                if printFlag:
                    print('-- radec_map does not contain filter %s' % color)
                continue
            elif rcid not in self.radec_map[filterid]:
                if printFlag:
                    print('-- radec_map %s does not have rcid %i' % (color, rcid))
                continue

            kdtree, object_id_arr = self.radec_map[filterid][rcid]
            query_ra, query_dec = self.ra, self.dec
            if is_pole and query_ra > 180:
                query_ra -= 360
            idx = kdtree.query_ball_point((query_ra, query_dec), radius_deg)
            if len(idx) == 0:
                continue
            sibling_object_id = int(object_id_arr[idx[0]])

            if sibling_object_id is None:
                if printFlag:
                    print('---- No siblings found for filter %i' % filterid)
            else:
                siblings_object_ids.append(sibling_object_id)

        self.set_siblings(siblings_object_ids, printFlag)

    def plot_lightcurve(self, filename=None, insert_radius=30):
        if filename is None:
            filename = '%s_%i_lc.png' % (self.filename.replace('.txt', ''),
                                         self.object_id)

        plot_object(filename=filename, object=self,
                    insert_radius=insert_radius)

    def plot_lightcurves(self, filename=None, insert_radius=30):
        if self.siblings is None:
            self.locate_siblings()

        if filename is None:
            filename = '%s_%s_lc_with_siblings.png' % (
                self.filename.replace('.txt', ''), self.object_id)

        source_dict = {'g': None, 'r': None, 'i': None,
                       self.color: self}
        for sibling in self.siblings:
            source_dict[sibling.color] = sibling

        plot_objects(filename=filename,
                     object_g=source_dict['g'],
                     object_r=source_dict['r'],
                     object_i=source_dict['i'],
                     insert_radius=insert_radius)


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
