#! /usr/bin/env python
"""
object.py
Each ZTF object can be represented as an instance of the Object class, along
with its metadata and lightcurve. Note that each ZTF object is only one color,
with a different color of the same astrophysical object labelled as a different
object. This class can find and save spatially coincident objects with the
locate_sibling function.
"""
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from zort.lightcurve import Lightcurve
from zort.utils import return_filename
from zort.utils import return_objects_filename
from zort.utils import return_rcid_map_filename


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
    coincident objects with the locate_sibling function.
    """

    def __init__(self, filename, lightcurve_position):
        # Load filenames and check for existence
        self.filename = return_filename(filename)
        self.objects_filename = return_objects_filename(filename)
        self.rcid_map_filename = return_rcid_map_filename(filename)

        self.lightcurve_position = int(lightcurve_position)
        params = self._load_params()
        self.objectid = params['objectid']
        self.nepochs = params['nepochs']
        self.filterid = params['filterid']
        self.fieldid = params['fieldid']
        self.rcid = params['rcid']
        self.ra = params['ra']
        self.dec = params['dec']
        self.color = self._return_filterid_color()
        self.lightcurve = self._load_lightcurve()
        self.sibling = None
        self.rcid_map = None
        # Tolerance for finding object siblings, in units of arcseconds
        self.sibling_tol_as = 2.0

    def __repr__(self):
        title = 'Filename: %s\n' % self.filename.split('/')[-1]
        title += 'Lightcurve Buffer Position: %i\n' % self.lightcurve_position
        title += 'Object ID: %i\n' % self.objectid
        title += 'Filter ID: %i | Color: %s\n' % (self.filterid, self.color)
        title += 'Ra/Dec: (%.5f, %.5f)\n' % (self.ra, self.dec)
        title += '%i Epochs passing quality cuts\n' % self.lightcurve.nepochs

        return title

    def _load_params(self):
        # Open lightcurve file
        file = open(self.filename, 'r')

        # Jump to the location of the object in the lightcurve file
        file.seek(self.lightcurve_position)

        line = file.readline()
        params = line.split()[1:]

        params_dict = dict()
        params_dict['objectid'] = int(params[0])
        params_dict['nepochs'] = int(params[1])
        params_dict['filterid'] = int(params[2])
        params_dict['fieldid'] = int(params[3])
        params_dict['rcid'] = int(params[4])
        params_dict['ra'] = float(params[5])
        params_dict['dec'] = float(params[6])
        return params_dict

    def _return_filterid_color(self):
        # Defined by ZTF convention
        if self.filterid == 1:
            return 'g'
        if self.filterid == 2:
            return 'r'

    def load_rcid_map(self):
        rcid_map_filename = self.rcid_map_filename
        rcid_map = pickle.load(open(rcid_map_filename, 'rb'))
        return rcid_map

    def return_sibling_filename(self):
        sibling_filename = self.filename.replace('.txt', '.siblings')
        return sibling_filename

    def _load_lightcurve(self):
        return Lightcurve(self.filename, self.lightcurve_position)

    def set_sibling(self, sibling_lightcurve_position, printFlag=False):
        # Assign the sibling to its own object instance
        self.sibling = Object(self.filename, sibling_lightcurve_position)

        if printFlag:
            print('---- Sibling found at %.5f, %.5f !' % (
                self.sibling.ra, self.sibling.dec))
        if printFlag:
            print('---- Original Color: %i | Sibling Color: %i' % (
                self.filterid, self.sibling.filterid))

    def test_radec(self, ra, dec):
        # See if the data is close enough to the object to be the
        # object's sibling

        # Tolerance is set in self.sibling_tol_as, in units of arcseconds
        tol_degree = self.sibling_tol_as / 3600.

        # Check to see if the data is within the correct declination range.
        # This saves time by exiting before making more expensive calculations.

        delta_dec = np.abs(dec - self.dec)
        if delta_dec > tol_degree:
            return 0

        # Calculate the full spherical distance between the data and
        # the object
        delta_ra = (ra - self.ra) * np.cos(np.radians(self.dec))
        delta = np.sqrt(delta_dec ** 2. + delta_ra ** 2.)

        # Determine if the sibling is within the set tolerance
        if delta <= tol_degree:
            return 1
        else:
            return 0

    def locate_sibling(self, printFlag=False):
        #
        if printFlag:
            print('Locating sibling for ZTF Object %i' % self.objectid)
            print('-- Object location: %.5f, %.5f ...' % (self.ra, self.dec))

        if self.rcid_map is None:
            self.rcid_map = self.load_rcid_map()

        # Searching for sibling in the opposite filtered section of
        # the rcid_map
        filterid = None
        if self.filterid == 1:
            filterid = 2
        elif self.filterid == 2:
            filterid = 1
        rcid = self.rcid

        try:
            buffer_start, buffer_end = self.rcid_map[filterid][rcid]
        except KeyError:
            print('** rcid_map missing filterid %i rcid %i ! **' % (filterid,
                                                                    rcid))
            return 1

        if printFlag:
            print('-- Searching between buffers %i and %i' % (buffer_start,
                                                              buffer_end))

        objects_fileobj = open(self.objects_filename, 'r')
        objects_fileobj.seek(buffer_start)

        sibling_lightcurve_position = None

        while True:
            line = objects_fileobj.readline()
            object_position = objects_fileobj.tell()

            # Check for end of file
            if not line:
                break

            # Check for end of rcid section of the file
            if object_position > buffer_end:
                break

            data = line.replace('\n', '').split(',')
            ra, dec = float(data[5]), float(data[6])
            status = self.test_radec(ra, dec)

            if status == 0:
                # No sibling found on this line
                continue
            elif status == 1:
                # Sibling found!
                sibling_lightcurve_position = data[-1]
                break

        objects_fileobj.close()

        if sibling_lightcurve_position is None:
            if printFlag:
                print('---- No sibling found')
        else:
            self.set_sibling(sibling_lightcurve_position)

    def plot_lightcurve(self, insert_radius=30):
        hmjd_min = np.min(self.lightcurve.hmjd) - 10
        hmjd_max = np.max(self.lightcurve.hmjd) + 10

        fig, ax = plt.subplots(1, 2, figsize=(12, 4))
        fig.subplots_adjust(hspace=0.4)

        ax[0].errorbar(self.lightcurve.hmjd, self.lightcurve.mag,
                       yerr=self.lightcurve.magerr,
                       ls='none', marker='.', color=self.color)
        ax[0].invert_yaxis()
        ax[0].set_xlim(hmjd_min, hmjd_max)
        ax[0].set_ylabel('Magnitude')
        ax[0].set_xlabel('Observation Date')
        ax[0].set_title('ZTF Object %i (%s band)' % (self.objectid,
                                                     self.color))

        hmjd0 = self.lightcurve.hmjd[np.argmin(self.lightcurve.mag)]
        hmjd_min_insert = hmjd0 - insert_radius
        hmjd_max_insert = hmjd0 + insert_radius
        hmjd_cond = (self.lightcurve.hmjd >= hmjd_min_insert) & (
                self.lightcurve.hmjd <= hmjd_max_insert)

        ax[1].errorbar(self.lightcurve.hmjd[hmjd_cond],
                       self.lightcurve.mag[hmjd_cond],
                       yerr=self.lightcurve.magerr[hmjd_cond],
                       ls='none', marker='.', color=self.color)
        ax[1].invert_yaxis()
        ax[1].set_xlim(hmjd_min_insert, hmjd_max_insert)
        ax[1].set_ylabel('Magnitude')
        ax[1].set_xlabel('Observation Date')
        ax[1].set_title('%i Days Around Peak' % insert_radius)

        fname = '%s-%i-lc.png' % (self.filename, self.lightcurve_position)
        fig.savefig(fname)
        print('---- Lightcurve saved: %s' % fname)

        plt.close(fig)
        return fname

    def plot_lightcurves(self, insert_radius=30):
        hmjd_min = np.min(self.lightcurve.hmjd) - 10
        hmjd_max = np.max(self.lightcurve.hmjd) + 10

        fig, ax = plt.subplots(2, 2, figsize=(12, 6))
        fig.subplots_adjust(top=0.92)
        fig.subplots_adjust(hspace=0.4)

        ax[0][0].errorbar(self.lightcurve.hmjd, self.lightcurve.mag,
                          yerr=self.lightcurve.magerr,
                          ls='none', marker='.', color=self.color)
        ax[0][0].invert_yaxis()
        ax[0][0].set_xlim(hmjd_min, hmjd_max)
        ax[0][0].set_ylabel('Magnitude')
        ax[0][0].set_xlabel('Observation Date')
        ax[0][0].set_title('ZTF Object %i (%s band)' % (self.objectid,
                                                        self.color))

        hmjd0 = self.lightcurve.hmjd[np.argmin(self.lightcurve.mag)]
        hmjd_min_insert = hmjd0 - insert_radius
        hmjd_max_insert = hmjd0 + insert_radius
        hmjd_cond = (self.lightcurve.hmjd >= hmjd_min_insert) & (
                self.lightcurve.hmjd <= hmjd_max_insert)

        ax[0][1].errorbar(self.lightcurve.hmjd[hmjd_cond],
                          self.lightcurve.mag[hmjd_cond],
                          yerr=self.lightcurve.magerr[hmjd_cond],
                          ls='none', marker='.', color=self.color)
        ax[0][1].invert_yaxis()
        ax[0][1].set_xlim(hmjd_min_insert, hmjd_max_insert)
        ax[0][1].set_ylabel('Magnitude')
        ax[0][1].set_xlabel('Observation Date')
        ax[0][1].set_title('%i Days Around Peak' % insert_radius)

        if self.sibling is None:
            self.locate_sibling()

        if self.sibling is not None:
            self.sibling._load_params()
            self.sibling._load_lightcurve()

            ax[1][0].errorbar(self.sibling.lightcurve.hmjd,
                              self.sibling.lightcurve.mag,
                              yerr=self.sibling.lightcurve.magerr,
                              ls='none',
                              marker='.',
                              color=self.sibling.color)
            ax[1][0].invert_yaxis()
            ax[1][0].set_xlim(hmjd_min, hmjd_max)
            ax[1][0].set_ylabel('Magnitude')
            ax[1][0].set_xlabel('Observation Date')
            ax[1][0].set_title('ZTF Object %i '
                               '(%s band)' % (self.sibling.objectid,
                                              self.sibling.color))

            hmjd_cond = (self.sibling.lightcurve.hmjd >= hmjd_min_insert) & \
                        (self.sibling.lightcurve.hmjd <= hmjd_max_insert)

            ax[1][1].errorbar(self.sibling.lightcurve.hmjd[hmjd_cond],
                              self.sibling.lightcurve.mag[hmjd_cond],
                              yerr=self.sibling.lightcurve.magerr[hmjd_cond],
                              ls='none',
                              marker='.',
                              color=self.sibling.color)
            ax[1][1].invert_yaxis()
            ax[1][1].set_xlim(hmjd_min_insert, hmjd_max_insert)
            ax[1][1].set_ylabel('Magnitude')
            ax[1][1].set_xlabel('Observation Date')
            ax[1][1].set_title('%i Days Around Peak' % insert_radius)

        else:
            for i in range(2):
                ax[1][i].axis('off')

                if self.rcid_map is None:
                    error_message = 'rcid_map missing'
                else:
                    error_message = 'sibling could not be found'

                ax[1][i].text(0.5, 0.5, error_message)

        fname = '%s-%i-lc-with_sibling.png' % (
            self.filename, self.lightcurve_position)
        fig.savefig(fname)
        print('---- Lightcurves saved: %s' % fname)

        plt.close(fig)
        return fname


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
