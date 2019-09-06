#! /usr/bin/env python
"""
radec.py
"""

from os import path
import numpy as np


def load_ZTF_CCD_corners(ra=0, dec=0):
    here = path.abspath(path.dirname(__file__))
    ZTF_CCD_layout_fname = '%s/data/ZTF_CCD_Layout.tbl' % here
    with open(ZTF_CCD_layout_fname, 'r') as f:
        lines = f.readlines()

    ZTF_CCD_layout = {}
    for line in lines[1:]:
        ra_offset, dec_offset, chip = line.split()
        ra_offset, dec_offset = float(ra_offset), float(dec_offset)
        ra_offset /= np.cos(np.radians(dec))
        ra_offset += ra
        dec_offset += dec
        if chip not in ZTF_CCD_layout.keys():
            ZTF_CCD_layout[chip] = [(ra_offset, dec_offset)]
        else:
            ZTF_CCD_layout[chip].append((ra_offset, dec_offset))

    return ZTF_CCD_layout


def return_CDD_corners(ra, dec):
    ZTF_CCD_layout = load_ZTF_CCD_corners(ra, dec)

    corners_dct = {}
    ccd_counter = 0
    for CCD, corners_tmp in ZTF_CCD_layout.items():
        corners = corners_tmp[1:]
        corners.append(corners_tmp[0])
        corners = np.array(corners)
        corners[:, 0] *= -1

        for quad in np.arange(4):
            top_right = ((corners[quad][0] + corners[0][0]) / 2.,
                         (corners[quad][1] + corners[1][1]) / 2.)
            top_left = ((corners[quad][0] + corners[1][0]) / 2.,
                        (corners[quad][1] + corners[1][1]) / 2.)
            bot_left = ((corners[quad][0] + corners[2][0]) / 2.,
                        (corners[quad][1] + corners[2][1]) / 2.)
            bot_right = ((corners[quad][0] + corners[3][0]) / 2.,
                         (corners[quad][1] + corners[3][1]) / 2.)

            quad_corners = np.array([[top_right[0], top_right[1]],
                                     [top_left[0], top_left[1]],
                                     [bot_left[0], bot_left[1]],
                                     [bot_right[0], bot_right[1]]])
            corners_dct[ccd_counter] = quad_corners

            ccd_counter += 1

    return corners_dct


def load_ZTF_fields():
    here = path.abspath(path.dirname(__file__))
    ZTF_fields_fname = '%s/data/ZTF_Fields.txt' % here
    data = np.genfromtxt(ZTF_fields_fname, skip_header=1,
                         dtype=[('id', int), ('ra', float), ('dec', float),
                                ('ebv', float), ('galLong', float),
                                ('galLat', float),
                                ('eclLong', float), ('eclLat', float),
                                ('entry', int)])
    return data
