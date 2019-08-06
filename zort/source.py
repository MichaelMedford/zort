#! /usr/bin/env python
"""
source.py
"""
import os
import pickle
import numpy as np
import portalocker as portalocker
import matplotlib.pyplot as plt
from lightcurve import Lightcurve


################################
#                              #
#  Source Class                #
#                              #
################################

class Source:

    def __init__(self, filename, buffer_position):
        try:
            self.filename = filename.decode()
        except AttributeError:
            self.filename = filename
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
        self.sibling_tol_as = 2.0

    def __repr__(self):
        title = 'ZTF Object %i\n' % self.objectid
        title += 'Color: %s\n' % self.color
        title += 'Ra/Dec: (%.5f, %.5f)' % (self.ra, self.dec)
        title += '%i Epochs' % self.lightcurve.nepochs

        return title

    def _load_params(self):
        try:
            file = open(self.filename, 'r')
        except FileNotFoundError as e:
            print(e)
            return None

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
        if self.filterid == 1:
            return 'g'
        if self.filterid == 2:
            return 'r'

    def load_rcid_map(self):
        rcid_map_filename = self.filename.replace('.txt', '.rcid_map')
        if not os.path.exists(rcid_map_filename):
            print('** rcid_map missing! **')
            return 1

        self.rcid_map = pickle.load(open(rcid_map_filename, 'rb'))

    def return_sources_filename(self):
        sources_filename = self.filename.replace('.txt', '.sources')
        return sources_filename

    def return_sibling_filename(self):
        sibling_filename = self.filename.replace('.txt', '.siblings')
        return sibling_filename

    def _load_lightcurve(self):
        return Lightcurve(self.filename, self.buffer_position)

    def return_sibling_file_status(self):
        filename = self.return_sibling_filename()
        if not os.path.exists(filename):
            print('** sibling file missing! **')
            return False
        else:
            return True

    def save_sibling(self):
        if self.sibling is None:
            print('** sibling not set! **')
            return 1

        filename = self.return_sibling_filename()
        with portalocker.Lock(filename, 'a', timeout=60) as f:
            f.write('%s,%s,%.1f\n' % (self.buffer_position,
                                      self.sibling.buffer_position,
                                      self.sibling_tol_as))

        print('---- Sibling saved')

    def load_sibling(self):
        if not self.return_sibling_file_status():
            return 1
        filename = self.return_sibling_filename()

        print('-- Loading sibling...')

        sibling_buffer_position = None
        for line in open(filename, 'r'):
            line_split = line.replace('\n', '').split(',')
            if int(line_split[0]) == self.buffer_position:
                sibling_buffer_position = int(line_split[1])
                break

        if sibling_buffer_position is None:
            print('-- Sibling could not be located')
            return 1

        self.sibling = Source(self.filename, sibling_buffer_position)
        print('-- Sibling loaded!')
        return 0

    def set_sibling(self, sibling_buffer_position):

        self.sibling = Source(self.filename, sibling_buffer_position)
        self.sibling.load_params()

        print('---- Sibling found at %.5f, %.5f !' % (
            self.sibling.ra, self.sibling.dec))
        print('---- Original Color: %i | Sibling Color: %i' % (
            self.filterid, self.sibling.filterid))

        self.save_sibling()

    def test_sibling(self, data):
        tol_degree = self.sibling_tol_as / 3600.
        ra, dec = float(data[5]), float(data[6])

        delta_dec = np.abs(dec - self.dec)
        if delta_dec > tol_degree:
            return 0

        delta_ra = (ra - self.ra) * np.cos(np.radians(self.dec))
        delta = np.sqrt(delta_dec ** 2. + delta_ra ** 2.)

        if delta <= tol_degree:
            return 1
        else:
            return 0

    def locate_sibling(self, attempt_to_load=True):
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

        # Searching for sibling in the opposite filtered section of the rcid_map
        filterid = None
        if self.filterid == 1:
            filterid = 2
        elif self.filterid == 2:
            filterid = 1
        rcid = self.rcid

        sources_filename = self.return_sources_filename()
        if not os.path.exists(sources_filename):
            print('** sources file missing! **')
            return 1

        try:
            buffer_start, buffer_end = self.rcid_map[filterid][rcid]
        except TypeError:
            print('** rcid_map missing filterid %i rcid %i ! **' % (filterid,
                                                                    rcid))
            return 1

        print('-- Searching between buffers %i and %i' % (
            buffer_start, buffer_end))

        sources_fileobj = open(sources_filename, 'r')
        sources_fileobj.seek(buffer_start)

        sibling_buffer_position = None

        while True:
            line = sources_fileobj.readline()
            object_buffer_position = sources_fileobj.tell()

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

        sources_fileobj.close()

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
            self.sibling.load_params()
            self.sibling.load_lightcurve()

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
