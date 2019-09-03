#! /usr/bin/env python
"""
photometry.py
A set of functions for performing photometric calculations on lightcurves.
"""

import numpy as np


def magnitudes_to_fluxes(m, sig_m, zero_point=22.0):
    """
    Given the mean and the standard deviation of a magnitude,
    assumed to be normally distributed, and a reference magnitude m0, this
    function returns the mean and the standard deviation of a Flux,
    which is log-normally distributed.
    Created by: Nathan Golovich <golovich1@llnl.gov>
    """

    # Calculate the mean and std. deviation for lnF which is assumed to be
    # normally distributed
    e = np.exp(1)
    mu_lnF = (zero_point - m) / (2.5 * np.log10(e))
    sig_lnF = sig_m / (2.5 * np.log10(e))

    # If lnF is normally distributed, F is log-normaly distributed with a mean
    # and root-variance given by
    mu_F = np.exp(mu_lnF + 0.5 * sig_lnF ** 2)
    sig_F = np.sqrt(
        (np.exp(sig_lnF ** 2) - 1) * np.exp(2 * mu_lnF + sig_lnF ** 2))

    return mu_F, sig_F


def fluxes_to_magnitudes(F, sig_F, zero_point=22.0):
    """
    Does the same thing as `magnitudes_to_fluxes` except in reverse.
    Created by: Nathan Golovich <golovich1@llnl.gov>
    """
    e = np.exp(1)
    sig_m = 2.5 * np.log10(e) * np.sqrt(np.log(sig_F ** 2 / F ** 2 + 1))
    mu_m = zero_point - 2.5 * np.log10(e) * (np.log(F) - 0.5 * np.log(
        1 + sig_F ** 2 / F ** 2))

    return mu_m, sig_m
