#! /usr/bin/env python
"""
radec.py
"""

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import os
import numpy as np


SHIFT_LOW_FIELD_IDS = set([1, 2, 5, 16, 33, 56, 85, 119, 157,
                           199, 245, 294, 396, 499, 550, 600,
                           648, 694, 736, 773, 806, 833, 854,
                           869, 878, 879, 880, 881, 1001, 1002,
                           1008, 1009, 1015, 1028, 1042, 1062,
                           1088, 1119, 1155, 1389, 1493, 1545,
                           1596, 1645, 1692, 1774, 1809, 1839,
                           1863, 1881, 1894, 1896])

SHIFT_HIGH_FIELD_IDS = set([4, 15, 32, 55, 84, 198, 395, 498,
                            735, 805, 832, 853, 868, 877, 1006,
                            1007, 1014, 1027, 1041, 1061, 1087,
                            1154, 1239, 1286, 1336, 1388, 1492,
                            1734, 1773, 1838, 1862, 1880, 1893,
                            1895, 1897])


def calculate_shift_low_and_high_field_ids():
    ZTF_fields = load_ZTF_fields()

    here = os.path.abspath(os.path.dirname(__file__))
    ZTF_CCD_layout_fname = '%s/data/ZTF_CCD_Layout.tbl' % here
    with open(ZTF_CCD_layout_fname, 'r') as f:
        lines = f.readlines()

    shift_low_field_ids = []
    shift_high_field_ids = []

    for ZTF_field in ZTF_fields:
        field_id = ZTF_field['id']
        field_ra = ZTF_field['ra']
        field_dec = ZTF_field['dec']

        wcs = WCS({'CTYPE1': 'RA---TAN',
                   'CTYPE2': 'DEC--TAN',
                   'CRPIX1': 0,
                   'CRPIX2': 0,
                   'CRVAL1': field_ra,
                   'CRVAL2': field_dec,
                   'CUNIT1': 'deg',
                   'CUNIT2': 'deg',
                   'CD1_1': 1,
                   'CD1_2': 0,
                   'CD2_1': 0,
                   'CD2_2': 1})

        shift_high = False
        shift_low = False
        for line in lines[1:]:
            ra_offset, dec_offset, chip = line.split()
            ra_offset, dec_offset = -float(ra_offset), float(dec_offset)
            ra_corner, dec_corner = wcs.all_pix2world(ra_offset, dec_offset, 1)

            if ra_offset > 0 and ra_corner < field_ra:
                shift_high = True
            elif ra_offset < 0 and ra_corner > field_ra:
                shift_low = True

        assert not (shift_high and shift_low)

        if shift_low:
            shift_low_field_ids.append(field_id)
        elif shift_high:
            shift_high_field_ids.append(field_id)

    return shift_low_field_ids, shift_high_field_ids


def return_shifted_ra(ra, field_id):
    if field_id in SHIFT_LOW_FIELD_IDS and ra > 180:
        ra_final = ra - 360
    elif field_id in SHIFT_HIGH_FIELD_IDS and ra < 180:
        ra_final = ra + 360
    else:
        ra_final = ra
    return ra_final


def load_ZTF_CCD_corners(field_id):

    ZTF_fields = load_ZTF_fields()
    ZTF_field = ZTF_fields[ZTF_fields['id'] == field_id]
    field_ra, field_dec = ZTF_field['ra'][0], ZTF_field['dec'][0]

    wcs = WCS({'CTYPE1': 'RA---TAN',
               'CTYPE2': 'DEC--TAN',
               'CRPIX1': 0,
               'CRPIX2': 0,
               'CRVAL1': field_ra,
               'CRVAL2': field_dec,
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

    shift_high = False
    shift_low = False
    ZTF_CCD_corners = {}
    for line in lines[1:]:
        ra_offset, dec_offset, chip = line.split()
        ra_offset, dec_offset = -float(ra_offset), float(dec_offset)
        chip = int(chip)
        ra_corner, dec_corner = wcs.all_pix2world(ra_offset, dec_offset, 1)

        if ra_offset > 0 and ra_corner < field_ra:
            ra_corner += 360
            shift_high = True
        elif ra_offset < 0 and ra_corner > field_ra:
            ra_corner -= 360
            shift_low = True

        if chip not in ZTF_CCD_corners.keys():
            ZTF_CCD_corners[chip] = [[ra_corner, dec_corner]]
        else:
            ZTF_CCD_corners[chip].append([ra_corner, dec_corner])

    for i in range(1, 17):
        ZTF_CCD_corners[i] = np.array(ZTF_CCD_corners[i])

    assert not (shift_high and shift_low)

    return ZTF_CCD_corners


def _calculate_two_point_midpoint(ra0, dec0, ra1, dec1, field_id):
    coord1 = SkyCoord(ra0 * u.deg, dec0 * u.deg, frame='icrs')
    coord2 = SkyCoord(ra1 * u.deg, dec1 * u.deg, frame='icrs')
    pa = coord1.position_angle(coord2)
    sep = coord1.separation(coord2)
    midpoint = coord1.directional_offset_by(pa, sep / 2)

    ra, dec = midpoint.ra.value, midpoint.dec.value
    ra_midpoint = return_shifted_ra(ra, field_id)

    return [ra_midpoint, dec]


def return_ZTF_RCID_corners(field_id):
    ZTF_CCD_corners = load_ZTF_CCD_corners(field_id)

    ZTF_RCID_corners = {}
    for CCD, CCD_corners_single in ZTF_CCD_corners.items():
        CCD_bottom_right = CCD_corners_single[0]
        CCD_top_right = CCD_corners_single[1]
        CCD_top_left = CCD_corners_single[2]
        CCD_bottom_left = CCD_corners_single[3]

        right_midpoint = _calculate_two_point_midpoint(*CCD_bottom_right,
                                                       *CCD_top_right,
                                                       field_id)
        left_midpoint = _calculate_two_point_midpoint(*CCD_top_left,
                                                      *CCD_bottom_left,
                                                      field_id)
        top_midpoint = _calculate_two_point_midpoint(*CCD_top_right,
                                                     *CCD_top_left,
                                                     field_id)
        bottom_midpoint = _calculate_two_point_midpoint(*CCD_bottom_right,
                                                        *CCD_bottom_left,
                                                        field_id)
        CCD_midpoint = _calculate_two_point_midpoint(*left_midpoint,
                                                     *right_midpoint,
                                                     field_id)


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
    dec_min_ra_max = ZTF_CCD_corners[1][0]
    dec_min_ra_min = ZTF_CCD_corners[4][3]
    dec_max_ra_min = ZTF_CCD_corners[16][2]
    dec_max_ra_max = ZTF_CCD_corners[13][1]

    polygon = Polygon([dec_min_ra_max,
                       dec_min_ra_min,
                       dec_max_ra_min,
                       dec_max_ra_max])
    point = Point(ra, dec)
    return polygon.contains(point)


def return_fields(ra, dec):
    fields = []
    ZTF_fields = load_ZTF_fields()
    for ZTF_field in ZTF_fields:
        field_id, field_ra, field_dec = ZTF_field['id'], \
                                        ZTF_field['ra'], \
                                        ZTF_field['dec']
        ZTF_CCD_corners = load_ZTF_CCD_corners(field_id)
        ra_test = return_shifted_ra(ra, field_id)

        if test_within_CCD_corners(ra_test, dec, ZTF_CCD_corners):
            fields.append(ZTF_field['id'])

    return fields


def test_within_RCID_corners(ra, dec, ZTF_RCID_corners_single):
    dec_min_ra_max = ZTF_RCID_corners_single[3]
    dec_min_ra_min = ZTF_RCID_corners_single[2]
    dec_max_ra_min = ZTF_RCID_corners_single[1]
    dec_max_ra_max = ZTF_RCID_corners_single[0]

    polygon = Polygon([dec_min_ra_max,
                       dec_min_ra_min,
                       dec_max_ra_min,
                       dec_max_ra_max])
    point = Point(ra, dec)
    return polygon.contains(point)


def return_rcid(field_id, ra, dec):
    ZTF_RCID_corners = return_ZTF_RCID_corners(field_id)
    ra_test = return_shifted_ra(ra, field_id)

    for rcid in range(64):
        ZTF_RCID_corners_single = ZTF_RCID_corners[rcid]
        if test_within_RCID_corners(ra_test, dec, ZTF_RCID_corners_single):
            return rcid

    return None
