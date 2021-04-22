#! /usr/bin/env python
"""
lightcurve.py
The observations of a ZTF object make up its lightcurve, held in the
Lightcurve class. Typically this class will be instantiated as an attribute of
an Object class.
"""

import numpy as np
import os
from zort.photometry import magnitudes_to_fluxes
from zort.utils import return_filename


################################
#                              #
#  Lightcurve Class            #
#                              #
################################

class Lightcurve:
    """
    The observations of a ZTF object make up its lightcurve, held in the
    Lightcurve class. Typically this class will be instantiated as an attribute
    of an Object class.
    """

    def __init__(self, filename, lightcurve_position,
                 apply_catmask=True, PS_g_minus_r=0,
                 lightcurve_file_pointer=None):
        # Load filenames and check for existence
        self.filename = return_filename(filename)

        self.lightcurve_position = lightcurve_position
        self.object_id = None  # set in self._load_lightcurve
        self.apply_catmask = apply_catmask
        self.PS_g_minus_r = PS_g_minus_r
        data = self._load_lightcurve(lightcurve_file_pointer)
        self.hmjd = data['hmjd']
        self.mag = data['mag']
        self.magerr = data['magerr']
        self.clrcoeff = data['clrcoeff']
        self.catflags = data['catflags']
        self.nepochs = int(len(self.mag))

        self._flux_fluxerr = None
        self._flux = None
        self._fluxerr =None
        self._mag_med = None
        self._mag_std = None
        self._flux_med = None
        self._flux_std = None

    def __repr__(self):
        title = 'Object ID: %s\n' % self.object_id
        title += 'N_epochs: %i\n' % self.nepochs

        return title

    @property
    def flux_fluxerr(self):
        if self._flux_fluxerr is None:
            flux, fluxerr = magnitudes_to_fluxes(self.mag, self.magerr)
            self._flux_fluxerr = flux, fluxerr
        return self._flux_fluxerr

    @property
    def flux(self):
        return self.flux_fluxerr[0]

    @property
    def fluxerr(self):
        return self.flux_fluxerr[1]
    
    @property
    def mag_med(self):
        if self._mag_med is None:
            self._mag_med = self._return_median(self.mag)
        return self._mag_med
    
    @property
    def mag_std(self):
        if self._mag_std is None:
            self._mag_std = self._return_std(self.mag)
        return self._mag_std

    @property
    def flux_med(self):
        if self._flux_med is None:
            self._flux_med = self._return_median(self.flux)
        return self._flux_med

    @property
    def flux_std(self):
        if self._flux_std is None:
            self._flux_std = self._return_std(self.flux)
        return self._flux_std

    def _load_lightcurve(self, lightcurve_file_pointer=None):
        """
        Loads the lightcurve from a lightcurve file, starting at the location
        of the object. The default is to apply a mask to any observations with
        a catflags >= 32768, following the recommendation of the ZTF Public Data
        Release website.
        """

        # Open file containing the lightcurve
        if lightcurve_file_pointer:
            file = lightcurve_file_pointer
            closeFlag = False
        else:
            file = open(self.filename, 'r')
            closeFlag = True

        # Jump to the location of the object in the lightcurve file
        file.seek(self.lightcurve_position)

        # load object_id
        line = file.readline()
        self.object_id = int(line.split()[1:][0])

        data = []
        for line in file:
            if line.startswith('#'):
                break
            else:
                data.append(tuple(line.split()))

        if closeFlag:
            file.close()

        # Assemble the data into a numpy recarray
        dtype = [('hmjd', float), ('mag', float), ('magerr', float),
                 ('clrcoeff', float), ('catflags', int)]
        data = np.array(data, dtype=dtype)

        # Apply the color correction
        data['mag'] = data['mag'] + data['clrcoeff'] * self.PS_g_minus_r

        # Apply the quality cut mask
        if self.apply_catmask:
            mask = data['catflags'] >= 32768
            data = data[~mask]

        # Remove points with bad values
        mask = np.isnan(data['hmjd'])
        mask += np.isnan(data['mag'])
        mask += np.isnan(data['magerr'])
        data = data[~mask]

        # Sort the observations by date
        cond = np.argsort(data['hmjd'])
        data = data[cond]

        return data

    def _return_median(self, data):
        if len(data) == 0:
            return None
        else:
            return np.median(data)

    def _return_std(self, data):
        if len(data) == 0:
            return None
        else:
            return np.std(data)


def save_lightcurves(filename, lightcurves, overwrite=False):
    if os.path.exists(filename) and not overwrite:
        print('%s already exists, exiting without saving objects. '
              'Set overwrite=True to enable writing over existing '
              'object lists.' % filename)
        return None

    with open(filename, 'w') as f:
        for lightcurve in lightcurves:
            f.write('%s,%i\n' % (lightcurve.filename,
                                 lightcurve.lightcurve_position))


def load_lightcurves(filename):
    lightcurves = []
    for line in open(filename, 'r'):
        filename, lightcurve_position = line.replace('\n', '').split(',')
        lightcurves.append(Lightcurve(filename, lightcurve_position))

    return lightcurves
