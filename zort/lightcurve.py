#! /usr/bin/env python
"""
lightcurve.py
The observations of a ZTF object make up its lightcurve, held in the
Lightcurve class. Typically this class will be instantiated as an attribute of
an Object class.
"""

from zort.photometry import magnitudes_to_fluxes
import numpy as np


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

    def __init__(self, filename, buffer_position, object_id, apply_mask=True):
        self.object_id = object_id
        self.filename = filename
        self.buffer_position = buffer_position
        data = self._load_lightcurve(apply_mask=apply_mask)
        self.hmjd = data['hmjd']
        self.mag = data['mag']
        self.magerr = data['magerr']
        flux, fluxerr = magnitudes_to_fluxes(self.mag, self.magerr)
        self.flux = flux
        self.fluxerr = fluxerr
        self.clrcoeff = data['clrcoeff']
        self.carflag = data['carflag']
        self.nepochs = float(len(self.mag))
        self.mag_med = self._return_median(self.mag)
        self.mag_std = self._return_std(self.mag)
        self.flux_med = self._return_median(self.flux)
        self.flux_std = self._return_std(self.flux)

    def __repr__(self):
        title = 'Object ID: %s\n' % self.object_id
        title += 'N_epochs: %i\n' % self.nepochs

        return title

    def _load_lightcurve(self, apply_mask=True):
        """
        Loads the lightcurve from a lightcurve file, starting at the location
        of the object. The default is to apply a mask to any observations with
        a 'carflag' != 0, following the recommendation of the ZTF Public Data
        Release website.
        """
        # Attempt to open file containing the lightcurve
        try:
            file = open(self.filename, 'r')
        except FileNotFoundError as e:
            print(e)
            return None

        # Jump to the location of the object in the lightcurve file
        file.seek(self.buffer_position)
        next(file)

        data = []

        for line in file:
            if line.startswith('#'):
                break
            else:
                data.append(tuple(line.split()))

        # Assemble the data into a numpy recarray
        dtype = [('hmjd', float), ('mag', float), ('magerr', float),
                 ('clrcoeff', float), ('carflag', int)]
        data = np.array(data, dtype=dtype)

        # Apply the quality cut mask
        if apply_mask:
            cond = data['carflag'] == 0
            data = data[cond]

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
