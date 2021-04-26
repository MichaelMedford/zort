#! /usr/bin/env python
"""
photometry.py
A set of functions for performing photometric calculations on lightcurves.
"""

import numpy as np


def magnitudes_to_fluxes(mag, magerr=None, zero_point=22.0):
    flux = 10 ** ((zero_point - mag) / 2.5)
    if magerr:
        fluxerr = flux * magerr / 1.086
    else:
        fluxerr = None
    return flux, fluxerr


def fluxes_to_magnitudes(flux, fluxerr=None, zero_point=22.0):
    mag = zero_point - 2.5 * np.log10(flux)
    if fluxerr:
        magerr = 1.086 * fluxerr / flux
    else:
        magerr = None
    return mag, magerr
