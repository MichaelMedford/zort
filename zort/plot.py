#! /usr/bin/env python
"""
plot.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def _plot_axis(ax, object, hmjd_min, hmjd_max, insert_radius):
    if object.color == 'i':
        color = 'k'
    else:
        color = object.color

    ax[0].errorbar(object.lightcurve.hmjd, object.lightcurve.mag,
                   yerr=object.lightcurve.magerr,
                   ls='none', marker='.', color=color)
    ax[0].invert_yaxis()
    ax[0].set_xlim(hmjd_min, hmjd_max)
    ax[0].set_ylabel('Magnitude')
    ax[0].set_xlabel('Observation Date')
    ax[0].set_title('ZTF Object %i (%s band)' % (object.object_id,
                                                 object.color))

    hmjd0 = object.lightcurve.hmjd[np.argmin(object.lightcurve.mag)]
    hmjd_min_insert = hmjd0 - insert_radius
    hmjd_max_insert = hmjd0 + insert_radius
    hmjd_cond = (object.lightcurve.hmjd >= hmjd_min_insert) & (
            object.lightcurve.hmjd <= hmjd_max_insert)

    ax[1].errorbar(object.lightcurve.hmjd[hmjd_cond],
                   object.lightcurve.mag[hmjd_cond],
                   yerr=object.lightcurve.magerr[hmjd_cond],
                   ls='none', marker='.', color=color)
    ax[1].invert_yaxis()
    ax[1].set_xlim(hmjd_min_insert, hmjd_max_insert)
    ax[1].set_ylabel('Magnitude')
    ax[1].set_xlabel('Observation Date')
    ax[1].set_title('%i Days Around Peak' % insert_radius)


def plot_object(filename, object, insert_radius=30):
    hmjd_min = np.min(object.lightcurve.hmjd) - 10
    hmjd_max = np.max(object.lightcurve.hmjd) + 10

    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    fig.subplots_adjust(hspace=0.4)

    _plot_axis(ax, object, hmjd_min, hmjd_max, insert_radius)

    fig.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0.05)
    print('---- Lightcurve saved: %s' % filename)
    plt.close(fig)


def plot_objects(filename, object_g=None, object_r=None,
                 object_i=None, insert_radius=30):
    if object_g is None and object_r is None and object_i is None:
        raise Exception('At least one object must be set to generate lightcurves.')

    objects = [object_g, object_r, object_i]
    objects = [obj for obj in objects if obj is not None]

    if len(objects) == 1:
        plot_object(objects[0], filename)
    elif len(objects) == 2:
        N_rows = 2
        figsize_height = 6
    else:
        N_rows = 3
        figsize_height = 9

    hmjd_min = min([o.lightcurve.hmjd.min() for o in objects]) - 10
    hmjd_max = max([o.lightcurve.hmjd.max() for o in objects]) + 10

    fig, ax = plt.subplots(N_rows, 2, figsize=(12, figsize_height))
    fig.subplots_adjust(top=0.92)
    fig.subplots_adjust(hspace=0.4)

    for i, object in enumerate(objects):
        _plot_axis(ax[i], object, hmjd_min, hmjd_max, insert_radius)

    fig.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0.05)
    print('---- Lightcurves saved: %s' % filename)
    plt.close(fig)
