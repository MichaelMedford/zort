#! /usr/bin/env python
"""
radec.py
"""

import os
import glob
import numpy as np
from zort.lightcurveFile import LightcurveFile


def load_ZTF_CCD_corners(ra=0, dec=0):
    here = os.path.abspath(os.path.dirname(__file__))
    ZTF_CCD_layout_fname = '%s/data/ZTF_CCD_Layout.tbl' % here
    with open(ZTF_CCD_layout_fname, 'r') as f:
        lines = f.readlines()

    ZTF_CCD_corners = {}
    for line in lines[1:]:
        ra_offset, dec_offset, chip = line.split()
        ra_offset, dec_offset = -float(ra_offset), float(dec_offset)
        chip = int(chip)
        ra_offset /= np.cos(np.radians(dec))
        ra_offset += ra
        dec_offset += dec
        if chip not in ZTF_CCD_corners.keys():
            ZTF_CCD_corners[chip] = [[ra_offset, dec_offset]]
        else:
            ZTF_CCD_corners[chip].append([ra_offset, dec_offset])

    for i in range(1, 17):
        ZTF_CCD_corners[i] = np.array(ZTF_CCD_corners[i])

    return ZTF_CCD_corners


def return_ZTF_RCID_corners(ra, dec):
    ZTF_CCD_corners = load_ZTF_CCD_corners(ra, dec)

    ZTF_RCID_corners = {}
    rcid_counter = 0
    for CCD, corners_tmp in ZTF_CCD_corners.items():
        corners = corners_tmp[1:]
        corners = np.vstack((corners, corners_tmp[0]))

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
            ZTF_RCID_corners[rcid_counter] = quad_corners

            rcid_counter += 1

    return ZTF_RCID_corners


def load_ZTF_fields():
    here = os.path.abspath(os.path.dirname(__file__))
    ZTF_fields_fname = '%s/data/ZTF_Fields.txt' % here
    ZTF_fields = np.genfromtxt(ZTF_fields_fname, skip_header=1,
                               dtype=[('id', int), ('ra', float),
                                      ('dec', float),
                                      ('ebv', float), ('galLong', float),
                                      ('galLat', float),
                                      ('eclLong', float), ('eclLat', float),
                                      ('entry', int)])
    return ZTF_fields


def test_within_CCD_corners(ra, dec, ZTF_CCD_corners):
    lower_right = ZTF_CCD_corners[1][0]
    lower_left = ZTF_CCD_corners[4][3]
    upper_right = ZTF_CCD_corners[13][1]
    upper_left = ZTF_CCD_corners[16][2]

    cond1 = ra >= np.min([lower_left[0], upper_left[0]])
    cond2 = ra <= np.max([lower_right[0], upper_right[0]])
    cond3 = dec >= np.min([lower_left[1], lower_right[1]])
    cond4 = dec <= np.min([upper_left[1], upper_right[1]])
    if cond1 and cond2 and cond3 and cond4:
        return True
    else:
        return False


def return_fields(ra, dec):
    fields = []
    ZTF_fields = load_ZTF_fields()
    for ZTF_field in ZTF_fields:
        field_ra, field_dec = ZTF_field['ra'], ZTF_field['dec']
        ZTF_CCD_corners = load_ZTF_CCD_corners(field_ra, field_dec)
        if test_within_CCD_corners(ra, dec, ZTF_CCD_corners):
            fields.append(ZTF_field['id'])

    return fields


def test_within_RCID_corners(ra, dec, ZTF_RCID_corners_single):
    lower_right = ZTF_RCID_corners_single[3]
    lower_left = ZTF_RCID_corners_single[2]
    upper_right = ZTF_RCID_corners_single[0]
    upper_left = ZTF_RCID_corners_single[1]

    cond1 = ra >= np.min([lower_left[0], upper_left[0]])
    cond2 = ra <= np.max([lower_right[0], upper_right[0]])
    cond3 = dec >= np.min([lower_left[1], lower_right[1]])
    cond4 = dec <= np.min([upper_left[1], upper_right[1]])
    if cond1 and cond2 and cond3 and cond4:
        return True
    else:
        return False


def return_rcid(field, ra, dec):
    ZTF_fields = load_ZTF_fields()
    ZTF_field = ZTF_fields[ZTF_fields['id'] == field]
    field_ra, field_dec = ZTF_field['ra'][0], ZTF_field['dec'][0]
    ZTF_RCID_corners = return_ZTF_RCID_corners(field_ra, field_dec)

    for rcid in range(64):
        ZTF_RCID_corners_single = ZTF_RCID_corners[rcid]
        if test_within_RCID_corners(ra, dec, ZTF_RCID_corners_single):
            return rcid

    print('No matching rcid found')
    return None


def locate_objects(data_dir, ra, dec, radius=3.):
    objects = []
    fields = return_fields(ra, dec)
    for field in fields:
        rcid = return_rcid(field, ra, dec)

        lightcurve_filenames = glob.glob('%s/field%06d*.txt' % (data_dir,
                                                               field))
        lightcurve_filenames = [f for f in lightcurve_filenames
                                if 'obs' not in f]
        for lightcurve_filename in lightcurve_filenames:
            lightcurveFile = LightcurveFile(lightcurve_filename)
            objects += lightcurveFile.locate_objects_by_radec(ra, dec, rcid,
                                                              radius=radius)

    return objects
