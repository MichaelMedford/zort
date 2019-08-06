#! /usr/bin/env python
"""
lightcurve.py
"""

from photometry import magnitudes_to_fluxes
import numpy as np


################################
#                              #
#  Lightcurve Class            #
#                              #
################################
class Lightcurve:

    def __init__(self, filename, buffer_position, apply_mask=True):
        self.filename = filename
        self.buffer_position = buffer_position
        data = self._load_lightcurve(filename, buffer_position,
                                     apply_mask=apply_mask)
        self.hmjd = data['hmjd']
        self.mag = data['mag']
        self.magerr = data['magerr']
        flux, fluxerr = magnitudes_to_fluxes(self.mag, self.magerr)
        self.flux = flux
        self.fluxerr = fluxerr
        self.clrcoeff = data['clrcoeff']
        self.carflag = data['carflag']
        self.nepochs = float(len(self.mag))
        self.mag_med = np.median(self.mag)
        self.mag_std = np.std(self.mag)
        self.flux_med = np.median(self.flux)
        self.flux_std = np.std(self.flux)

    def __repr__(self):
        title = 'Filename: %s\n' % self.filename
        title += 'Buffer Position: %s\n' % self.buffer_position
        title += 'N_epochs: %i' % self.nepochs

        return title

    def _load_lightcurve(self, filename, buffer_position, apply_mask=True):
        file = open(filename, 'r')
        file.seek(buffer_position)
        next(file)

        data = []

        for line in file:
            if line.startswith('#'):
                break
            else:
                data.append(tuple(line.split()))

        dtype = [('hmjd', float), ('mag', float), ('magerr', float),
                 ('clrcoeff', float), ('carflag', int)]
        data = np.array(data, dtype=dtype)

        if apply_mask:
            cond = data['carflag'] == 0
            data = data[cond]

        cond = np.argsort(data['hmjd'])
        data = data[cond]

        return data
