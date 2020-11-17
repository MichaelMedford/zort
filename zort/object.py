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
import matplotlib.pyplot as plt
from zort.lightcurve import Lightcurve
from zort.utils import return_filename, return_objects_filename, \
    return_rcid_map_filename, filterid_dict


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
    coincident objects with the locate_siblingss function.
    """

    def __init__(self, filename, lightcurve_position, apply_catmask=False):
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
        self.apply_catmask = apply_catmask
        self.lightcurve = self._load_lightcurve()
        self.siblings = []
        self.rcid_map = None
        # Tolerance for finding object siblingss, in units of arcseconds
        self.sibling_tol_as = 2.0

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
        return filterid_dict[self.filterid]

    def load_rcid_map(self):
        rcid_map_filename = self.rcid_map_filename
        rcid_map = pickle.load(open(rcid_map_filename, 'rb'))
        return rcid_map

    def return_siblings_filename(self):
        siblings_filename = self.filename.replace('.txt', '.siblings')
        return siblings_filename

    def _load_lightcurve(self):
        return Lightcurve(self.filename, self.lightcurve_position,
                          apply_catmask=self.apply_catmask)

    def set_siblings(self, siblings_lightcurve_position, printFlag=False):
        # Assign the siblings to its own object instance
        sibling = Object(self.filename, siblings_lightcurve_position)
        self.siblings.append(sibling)

        if printFlag:
            print('---- Sibling found at %.5f, %.5f !' % (
                sibling.ra, sibling.dec))
            print('---- Original Color: %s | Sibling Color: %s' % (
                self.color, sibling.color))

    def test_radec(self, ra, dec):
        # See if the data is close enough to the object to be the
        # object's siblings

        # Tolerance is set in self.sibling_tol_as, in units of arcseconds
        tol_degree = self.sibling_tol_as / 3600.

        # Check to see if the data is within the correct declination range.
        # This saves time by exiting before making more expensive calculations.

        delta_dec = np.abs(dec - self.dec)
        if delta_dec > tol_degree:
            return False

        # Calculate the full spherical distance between the data and
        # the object
        delta_ra = (ra - self.ra) * np.cos(np.radians(self.dec))
        delta = np.sqrt(delta_dec ** 2. + delta_ra ** 2.)

        # Determine if the siblings is within the set tolerance
        if delta <= tol_degree:
            return True
        else:
            return False

    def locate_siblings(self, skip_filterids=None, printFlag=False):
        #
        if printFlag:
            print('Locating siblings for ZTF Object %i' % self.objectid)
            print('-- Object location: %.5f, %.5f ...' % (self.ra, self.dec))

        if self.rcid_map is None:
            self.rcid_map = self.load_rcid_map()

        # Searching for siblings in the opposite
        # filtered sections of the rcid_map
        sibling_filterids = [i for i in [1, 2, 3] if i != self.filterid]
        if skip_filterids:
            sibling_filterids = [i for i in sibling_filterids
                                 if i not in skip_filterids]
        rcid = self.rcid

        for filterid in sibling_filterids:
            color = filterid_dict[filterid]
            if filterid not in self.rcid_map:
                if printFlag:
                    print('-- rcid_map does not contain filter %s' % color)
                continue
            elif rcid not in self.rcid_map[filterid]:
                if printFlag:
                    print('-- rcid_map %s does not have rcid %i' % (color, rcid))
                continue

            buffer_start, buffer_end = self.rcid_map[filterid][rcid]

            if printFlag:
                print('-- Searching filter %s between '
                      'buffers %i and %i' % (filterid_dict[filterid],
                                             buffer_start, buffer_end))

            objects_fileobj = open(self.objects_filename, 'r')
            objects_fileobj.seek(buffer_start)

            siblings_lightcurve_position = None

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
                    # No siblings found on this line
                    continue
                elif status == 1:
                    # Sibling found!
                    siblings_lightcurve_position = data[-1]
                    break

            objects_fileobj.close()

            if siblings_lightcurve_position is None:
                if printFlag:
                    print('---- No siblings found for filter %i' % filterid)
            else:
                self.set_siblings(siblings_lightcurve_position, printFlag)

    def plot_lightcurve(self, filename=None, insert_radius=30):
        hmjd_min = np.min(self.lightcurve.hmjd) - 10
        hmjd_max = np.max(self.lightcurve.hmjd) + 10

        if self.color == 'i':
            color = 'k'
        else:
            color = self.color

        fig, ax = plt.subplots(1, 2, figsize=(12, 4))
        fig.subplots_adjust(hspace=0.4)

        ax[0].errorbar(self.lightcurve.hmjd, self.lightcurve.mag,
                       yerr=self.lightcurve.magerr,
                       ls='none', marker='.', color=color)
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
                       ls='none', marker='.', color=color)
        ax[1].invert_yaxis()
        ax[1].set_xlim(hmjd_min_insert, hmjd_max_insert)
        ax[1].set_ylabel('Magnitude')
        ax[1].set_xlabel('Observation Date')
        ax[1].set_title('%i Days Around Peak' % insert_radius)

        if filename is None:
            filename = '%s-%i-lc.png' % (self.filename, self.lightcurve_position)
        fig.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0.05)
        print('---- Lightcurve saved: %s' % filename)

        plt.close(fig)
        return filename

    def plot_lightcurves(self, filename=None, insert_radius=30):
        hmjd_min = np.min(self.lightcurve.hmjd) - 10
        hmjd_max = np.max(self.lightcurve.hmjd) + 10

        if self.siblings is None:
            self.locate_siblings()

        if len(self.siblings) == 0:
            self.plot_lightcurve(insert_radius=insert_radius)
            return
        elif len(self.siblings) == 1:
            N_rows = 2
            figsize_height = 6
        else:
            N_rows = 3
            figsize_height = 9

        if self.color == 'i':
            color = 'k'
        else:
            color = self.color

        fig, ax = plt.subplots(N_rows, 2, figsize=(12, figsize_height))
        fig.subplots_adjust(top=0.92)
        fig.subplots_adjust(hspace=0.4)

        ax[0][0].errorbar(self.lightcurve.hmjd, self.lightcurve.mag,
                          yerr=self.lightcurve.magerr,
                          ls='none', marker='.', color=color)
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
                          ls='none', marker='.', color=color)
        ax[0][1].invert_yaxis()
        ax[0][1].set_xlim(hmjd_min_insert, hmjd_max_insert)
        ax[0][1].set_ylabel('Magnitude')
        ax[0][1].set_xlabel('Observation Date')
        ax[0][1].set_title('%i Days Around Peak' % insert_radius)

        for i, sibling in enumerate(self.siblings, 1):
            sibling._load_params()
            sibling._load_lightcurve()
            if sibling.color == 'i':
                color = 'k'
            else:
                color = sibling.color

            ax[i][0].errorbar(sibling.lightcurve.hmjd,
                              sibling.lightcurve.mag,
                              yerr=sibling.lightcurve.magerr,
                              ls='none',
                              marker='.',
                              color=color)
            ax[i][0].invert_yaxis()
            ax[i][0].set_xlim(hmjd_min, hmjd_max)
            ax[i][0].set_ylabel('Magnitude')
            ax[i][0].set_xlabel('Observation Date')
            ax[i][0].set_title('ZTF Object %i '
                               '(%s band)' % (sibling.objectid,
                                              sibling.color))

            hmjd_cond = (sibling.lightcurve.hmjd >= hmjd_min_insert) & \
                        (sibling.lightcurve.hmjd <= hmjd_max_insert)

            ax[i][1].errorbar(sibling.lightcurve.hmjd[hmjd_cond],
                              sibling.lightcurve.mag[hmjd_cond],
                              yerr=sibling.lightcurve.magerr[hmjd_cond],
                              ls='none',
                              marker='.',
                              color=color)
            ax[i][1].invert_yaxis()
            ax[i][1].set_xlim(hmjd_min_insert, hmjd_max_insert)
            ax[i][1].set_ylabel('Magnitude')
            ax[i][1].set_xlabel('Observation Date')
            ax[i][1].set_title('%i Days Around Peak' % insert_radius)

        if filename is None:
            filename = '%s-%i-lc-with_siblings.png' % (
                self.filename, self.lightcurve_position)
        fig.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0.05)
        print('---- Lightcurves saved: %s' % filename)

        plt.close(fig)
        return filename


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
