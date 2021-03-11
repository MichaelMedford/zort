#! /usr/bin/env python
"""
fit.py
"""

import numpy as np
from zort.photometry import fluxes_to_magnitudes, magnitudes_to_fluxes


def return_q(t_arr, t0, t_eff):
    return 1 + (((t_arr - t0) / t_eff)*((t_arr - t0) / t_eff))


def return_amplification_one(q):
    return 1 / np.sqrt(q)


def return_amplification_two(q):
    return 1 / np.sqrt((1 - (1 / (((q / 2) + 1)*((q / 2) + 1)))))


def _amplification(q, a_type):
    if a_type == 'one':
        a = return_amplification_one(q)
    elif a_type == 'two':
        a = return_amplification_two(q)
    else:
        raise Exception('a_type must be either "one" or "two"')
    return a


def return_amplification(t_arr, t0, t_eff, a_type):
    q = return_q(t_arr, t0, t_eff)
    a = _amplification(q, a_type)
    return a


def return_flux_model(t_arr, t0, t_eff, a_type, f0, f1):
    a = return_amplification(t_arr, t0, t_eff, a_type)
    return f1 * a + f0


def return_mag_model(t_arr, t0, t_eff, a_type, f0, f1, zero_point=22.0):
    flux_model = return_flux_model(t_arr, t0, t_eff, a_type, f0, f1)
    return -2.5 * np.log10(flux_model) + zero_point
