#! /usr/bin/env python
"""
radec.py
"""

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import os
import numpy as np


def load_ZTF_CCD_corners(ra=0, dec=0):
    wcs = WCS({'CTYPE1': 'RA---TAN',
               'CTYPE2': 'DEC--TAN',
               'CRPIX1': 0,
               'CRPIX2': 0,
               'CRVAL1': ra,
               'CRVAL2': dec,
               'CUNIT1': 'deg',
               'CUNIT2': 'deg',
               'CD1_1': 1,
               'CD1_2': 0,
               'CD2_1': 0,
               'CD2_2': 1})

    here = os.path.abspath(os.path.dirname(__file__))
    ZTF_CCD_layout_fname = '%s/data/ZTF_CCD_Layout.tbl' % here
    with open(ZTF_CCD_layout_fname, 'r') as f:
        lines = f.readlines()

    ZTF_CCD_corners = {}
    for line in lines[1:]:
        ra_offset, dec_offset, chip = line.split()
        ra_offset, dec_offset = -float(ra_offset), float(dec_offset)
        chip = int(chip)
        ra_corner, dec_corner = wcs.all_pix2world(ra_offset, dec_offset, 1)
        if chip not in ZTF_CCD_corners.keys():
            ZTF_CCD_corners[chip] = [[ra_corner, dec_corner]]
        else:
            ZTF_CCD_corners[chip].append([ra_corner, dec_corner])

    for i in range(1, 17):
        ZTF_CCD_corners[i] = np.array(ZTF_CCD_corners[i])

    return ZTF_CCD_corners


def _calculate_two_point_midpoint(ra0, dec0, ra1, dec1):
    coord1 = SkyCoord(ra0 * u.deg, dec0 * u.deg, frame='icrs')
    coord2 = SkyCoord(ra1 * u.deg, dec1 * u.deg, frame='icrs')
    pa = coord1.position_angle(coord2)
    sep = coord1.separation(coord2)
    midpoint = coord1.directional_offset_by(pa, sep / 2)
    return midpoint.ra.value, midpoint.dec.value


def return_ZTF_RCID_corners(ra, dec):
    ZTF_CCD_corners = load_ZTF_CCD_corners(ra, dec)

    ZTF_RCID_corners = {}
    for CCD, CCD_corners_single in ZTF_CCD_corners.items():
        CCD_bottom_right = CCD_corners_single[0]
        CCD_top_right = CCD_corners_single[1]
        CCD_top_left = CCD_corners_single[2]
        CCD_bottom_left = CCD_corners_single[3]

        right_midpoint = _calculate_two_point_midpoint(*CCD_bottom_right,
                                                       *CCD_top_right)
        left_midpoint = _calculate_two_point_midpoint(*CCD_top_left,
                                                      *CCD_bottom_left)
        top_midpoint = _calculate_two_point_midpoint(*CCD_top_right,
                                                     *CCD_top_left)
        bottom_midpoint = _calculate_two_point_midpoint(*CCD_bottom_right,
                                                        *CCD_bottom_left)
        CCD_midpoint = _calculate_two_point_midpoint(*left_midpoint,
                                                     *right_midpoint)

        for quad in np.arange(4):
            if quad == 0:
                quad_corners = np.array([CCD_top_right,
                                         top_midpoint,
                                         CCD_midpoint,
                                         right_midpoint])
            elif quad == 1:
                quad_corners = np.array([top_midpoint,
                                         CCD_top_left,
                                         left_midpoint,
                                         CCD_midpoint])
            elif quad == 2:
                quad_corners = np.array([CCD_midpoint,
                                         left_midpoint,
                                         CCD_bottom_left,
                                         bottom_midpoint])
            elif quad == 3:
                quad_corners = np.array([right_midpoint,
                                         CCD_midpoint,
                                         bottom_midpoint,
                                         CCD_bottom_right])

            rcid = 4 * (CCD - 1) + quad
            ZTF_RCID_corners[rcid] = quad_corners

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
