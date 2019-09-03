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
import portalocker as portalocker
import matplotlib.pyplot as plt
from zort.lightcurve import Lightcurve


################################
#                              #
#  Object Class                #
#                              #
################################

class Object:
    """
    Each ZTF object can be represented as an instance of the Object class,
    along with its parameters and lightcurve. Note that each ZTF object is only
    one color, with a different color of the same astrophysical object
    labelled as a different object. This class can find and save spatially
    coincident objects with the locate_sibling function.
    """

    def __init__(self, filename, buffer_position):
        self.filename = self._set_filename(filename)
        self.buffer_position = int(buffer_position)
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
        title += 'Buffer Position: %i\n' % self.buffer_position
        title += 'Object ID: %i\n' % self.objectid
        title += 'Color: %s\n' % self.color
        title += 'Ra/Dec: (%.5f, %.5f)\n' % (self.ra, self.dec)
        title += '%i Epochs passing quality cuts\n' % self.lightcurve.nepochs

        return title

    def _set_filename(self, filename):
        try:
            filename = filename.decode()
        except AttributeError:
            filename = filename

        if '/' not in filename:
            filename = os.getenv('ZTF_LC_DATA') + '/' + filename

        return filename

    def _load_params(self):
        # Attempt to open file containing the parameters
        try:
            file = open(self.filename, 'r')
        except FileNotFoundError as e:
            print(e)
            return None

        # Jump to the location of the object in the lightcurve file
        file.seek(self.buffer_position)

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
        # Attempt to locate the rcid map for this object's file
        rcid_map_filename = self.filename.replace('.txt', '.rcid_map')
        if not os.path.exists(rcid_map_filename):
            print('** rcid_map missing! **')
            return 1

        self.rcid_map = pickle.load(open(rcid_map_filename, 'rb'))

    def return_objects_filename(self):
        objects_filename = self.filename.replace('.txt', '.objects')
        return objects_filename

    def return_sibling_filename(self):
        sibling_filename = self.filename.replace('.txt', '.siblings')
        return sibling_filename

    def _load_lightcurve(self):
        return Lightcurve(self.filename, self.buffer_position, self.objectid)

    def return_sibling_file_status(self):
        # Attempt to locate the sibling file for this object's file
        filename = self.return_sibling_filename()
        if not os.path.exists(filename):
            print('** sibling file missing! **')
            return False
        else:
            return True

    def save_sibling(self):
        # Can only save a sibling is one is already assigned to this object
        if self.sibling is None:
            print('** sibling not set! **')
            return 1

        filename = self.return_sibling_filename()

        # Portalocker guarantees that if parallel processes are attempting to
        # write siblings to the sibling file that they will not collide with
        # each other. While this append is occuring the file is locked from
        # any process that attempts to open it with portalocker. Attempts to
        # open the file without portalocker will still success but could cause
        # a collision.
        with portalocker.Lock(filename, 'a', timeout=60) as f:
            f.write('%s,%s,%.1f\n' % (self.buffer_position,
                                      self.sibling.buffer_position,
                                      self.sibling_tol_as))

        print('---- Sibling saved')

    def load_sibling(self):
        # Attempt to locate the sibling file for this object's file
        if not self.return_sibling_file_status():
            return 1

        filename = self.return_sibling_filename()

        print('-- Loading sibling...')

        # Loop through the sibling file until the object is located
        sibling_buffer_position = None
        for line in open(filename, 'r'):
            line_split = line.replace('\n', '').split(',')
            if int(line_split[0]) == self.buffer_position:
                sibling_buffer_position = int(line_split[1])
                break

        if sibling_buffer_position is None:
            print('-- Sibling could not be loaded')
            return 1

        # Assign the sibling to its own object instance
        self.sibling = Object(self.filename, sibling_buffer_position)
        print('-- Sibling loaded!')
        return 0

    def set_sibling(self, sibling_buffer_position):
        # Assign the sibling to its own object instance
        self.sibling = Object(self.filename, sibling_buffer_position)

        print('---- Sibling found at %.5f, %.5f !' % (
            self.sibling.ra, self.sibling.dec))
        print('---- Original Color: %i | Sibling Color: %i' % (
            self.filterid, self.sibling.filterid))

        self.save_sibling()

    def test_sibling(self, data):
        # See if the data is close enough to the object to be the
        # object's sibling

        # Tolerance is set in self.sibling_tol_as, in units of arcseconds
        tol_degree = self.sibling_tol_as / 3600.
        ra, dec = float(data[5]), float(data[6])

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

    def locate_sibling(self, attempt_to_load=True):
        #
        print('Locating sibling for ZTF Object %i' % self.objectid)
        print('-- Object location: %.5f, %.5f ...' % (self.ra, self.dec))

        if attempt_to_load:
            status = self.load_sibling()
            if status == 0:
                return

        if self.rcid_map is None:
            status = self.load_rcid_map()
            if status == 1:
                return

        # Searching for sibling in the opposite filtered section of
        # the rcid_map
        filterid = None
        if self.filterid == 1:
            filterid = 2
        elif self.filterid == 2:
            filterid = 1
        rcid = self.rcid

        objects_filename = self.return_objects_filename()
        if not os.path.exists(objects_filename):
            print('** objects file missing! **')
            return 1

        try:
            buffer_start, buffer_end = self.rcid_map[filterid][rcid]
        except TypeError:
            print('** rcid_map missing filterid %i rcid %i ! **' % (filterid,
                                                                    rcid))
            return 1

        print('-- Searching between buffers %i and %i' % (
            buffer_start, buffer_end))

        objects_fileobj = open(objects_filename, 'r')
        objects_fileobj.seek(buffer_start)

        sibling_buffer_position = None

        while True:
            line = objects_fileobj.readline()
            object_buffer_position = objects_fileobj.tell()

            # Check for end of file
            if not line:
                break

            # Check for end of rcid section of the file
            if object_buffer_position >= buffer_end:
                break

            data = line.replace('\n', '').split(',')
            status = self.test_sibling(data)

            if status == 0:
                # No sibling found on this line
                continue
            elif status == 1:
                # Sibling found!
                sibling_buffer_position = data[-1]
                break

        objects_fileobj.close()

        if sibling_buffer_position is None:
            print('---- No sibling found')
        else:
            self.set_sibling(sibling_buffer_position)

    def plot_lightcurve(self):
        fig, ax = plt.subplots()
        ax.errorbar(self.lightcurve.hmjd, self.lightcurve.mag,
                    yerr=self.lightcurve.magerr,
                    ls='none', color=self.color)
        ax.invert_yaxis()

        title = 'o%i_f%i' % (self.objectid, self.filterid)
        fig.suptitle(title)

        fname = '%s-%i-lc.png' % (self.filename, self.buffer_position)
        fig.savefig(fname)
        print('---- Lightcurve saved: %s' % fname)

        plt.close(fig)

    def plot_lightcurves(self, insert_radius=30):
        hmjd_min = np.min(self.lightcurve.hmjd) - 15
        hmjd_max = np.max(self.lightcurve.hmjd) + 15

        fig, ax = plt.subplots(2, 2, figsize=(10, 6))
        fig.subplots_adjust(top=0.92)
        fig.subplots_adjust(hspace=0.4)

        ax[0][0].errorbar(self.lightcurve.hmjd, self.lightcurve.mag,
                          yerr=self.lightcurve.magerr,
                          ls='none', color=self.color)
        ax[0][0].invert_yaxis()
        ax[0][0].set_xlim(hmjd_min, hmjd_max)
        ax[0][0].set_ylabel('Magnitude')
        ax[0][0].set_xlabel('Observation Date')
        ax[0][0].set_title('ZTF Object %i' % self.objectid)

        hmjd0 = self.lightcurve.hmjd[np.argmin(self.lightcurve.mag)]
        hmjd_min_insert = hmjd0 - insert_radius
        hmjd_max_insert = hmjd0 + insert_radius
        hmjd_cond = (self.lightcurve.hmjd >= hmjd_min_insert) & (
                self.lightcurve.hmjd <= hmjd_max_insert)

        ax[0][1].errorbar(self.lightcurve.hmjd[hmjd_cond],
                          self.lightcurve.mag[hmjd_cond],
                          yerr=self.lightcurve.magerr[hmjd_cond],
                          ls='none', color=self.color)
        ax[0][1].invert_yaxis()
        ax[0][1].set_xlim(hmjd_min_insert, hmjd_max_insert)
        ax[0][1].set_ylabel('Magnitude')
        ax[0][1].set_xlabel('Observation Date')

        if self.sibling is None:
            self.locate_sibling()

        if self.sibling is not None:
            self.sibling._load_params()
            self.sibling._load_lightcurve()

            ax[1][0].errorbar(self.sibling.lightcurve.hmjd,
                              self.sibling.lightcurve.mag,
                              yerr=self.sibling.lightcurve.magerr,
                              ls='none',
                              color=self.sibling.color)
            ax[1][0].invert_yaxis()
            ax[1][0].set_xlim(hmjd_min, hmjd_max)
            ax[1][0].set_ylabel('Magnitude')
            ax[1][0].set_xlabel('Observation Date')
            ax[1][0].set_title('ZTF Object %i' % self.sibling.objectid)

            hmjd_cond = (self.sibling.lightcurve.hmjd >= hmjd_min_insert) & \
                        (self.sibling.lightcurve.hmjd <= hmjd_max_insert)

            ax[1][1].errorbar(self.sibling.lightcurve.hmjd[hmjd_cond],
                              self.sibling.lightcurve.mag[hmjd_cond],
                              yerr=self.sibling.lightcurve.magerr[hmjd_cond],
                              ls='none',
                              color=self.sibling.color)
            ax[1][1].invert_yaxis()
            ax[1][1].set_xlim(hmjd_min_insert, hmjd_max_insert)
            ax[1][1].set_ylabel('Magnitude')
            ax[1][1].set_xlabel('Observation Date')

        else:
            for i in range(2):
                ax[1][i].axis('off')

                if self.rcid_map is None:
                    error_message = 'rcid_map missing'
                else:
                    error_message = 'sibling could not be found'

                ax[1][i].text(0.5, 0.5, error_message)

        fname = '%s-%i-lc-with_sibling.png' % (
            self.filename, self.buffer_position)
        fig.savefig(fname)
        print('---- Lightcurves saved: %s' % fname)
        plt.close(fig)
