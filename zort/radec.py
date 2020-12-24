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


# statically stored to save computation
# calculated with +- 10 degrees from poles
# can be re-generated with `generate_pole_field_ids`
POLE_FIELD_IDS = set([1,   33,   55,   56,   84,   85,  119,  120,  156,
                      157,  198, 199,  200,  244,  245,  246,  293,  294,
                      295,  344,  345,  394, 395,  396,  397,  446,  447,
                      497,  498,  499,  500,  549,  550, 551,  599,  600,
                      601,  647,  648,  649,  693,  694,  735,  736, 772,
                      773,  805,  806,  832,  833,  853,  878,  880, 1015,
                      1041, 1061, 1062, 1087, 1088, 1119, 1154, 1155, 1156,
                      1195, 1196, 1238, 1239, 1240, 1286, 1287, 1335, 1336,
                      1337, 1387, 1388, 1389, 1390, 1440, 1441, 1491, 1492,
                      1493, 1494, 1544, 1545, 1546, 1595, 1596, 1597, 1644,
                      1645, 1646, 1691, 1692, 1734, 1735, 1773, 1774, 1808,
                      1809, 1838, 1839, 1862, 1880, 1881])


def generate_pole_field_ids():
    ZTF_fields = load_ZTF_fields()
    ra = ZTF_fields['ra']
    cond = (ra <= 10) + (ra >= (360 - 10))
    return ZTF_fields['id'][cond]


def field_is_pole(field_id):
    return field_id in POLE_FIELD_IDS


def lightcurve_file_is_pole(lightcurve_file):
    field = int(lightcurve_file.split('_')[0].replace('field', ''))
    return field_is_pole(field)


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

    is_pole = field_is_pole(field_id)

    ZTF_CCD_corners = {}
    for line in lines[1:]:
        ra_offset, dec_offset, chip = line.split()
        ra_offset, dec_offset = -float(ra_offset), float(dec_offset)
        chip = int(chip)
        ra_corner, dec_corner = wcs.all_pix2world(ra_offset, dec_offset, 1)
        if is_pole and ra_corner > 180:
            ra_corner -= 360
        if chip not in ZTF_CCD_corners.keys():
            ZTF_CCD_corners[chip] = [[ra_corner, dec_corner]]
        else:
            ZTF_CCD_corners[chip].append([ra_corner, dec_corner])

    for i in range(1, 17):
        ZTF_CCD_corners[i] = np.array(ZTF_CCD_corners[i])

    return ZTF_CCD_corners


def _calculate_two_point_midpoint(ra0, dec0, ra1, dec1, field_id=None):
    coord1 = SkyCoord(ra0 * u.deg, dec0 * u.deg, frame='icrs')
    coord2 = SkyCoord(ra1 * u.deg, dec1 * u.deg, frame='icrs')
    pa = coord1.position_angle(coord2)
    sep = coord1.separation(coord2)
    midpoint = coord1.directional_offset_by(pa, sep / 2)

    ra, dec = midpoint.ra.value, midpoint.dec.value
    if field_id and field_is_pole(field_id) and ra > 180:
        ra -= 360
    return ra, dec


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
    lower_right = ZTF_CCD_corners[1][0]
    lower_left = ZTF_CCD_corners[4][3]
    upper_right = ZTF_CCD_corners[13][1]
    upper_left = ZTF_CCD_corners[16][2]

    polygon = Polygon([lower_right,
                       lower_left,
                       upper_left,
                       upper_right])
    point = Point(ra, dec)
    return polygon.contains(point)


def return_fields(ra, dec):
    fields = []
    ZTF_fields = load_ZTF_fields()
    for ZTF_field in ZTF_fields:
        field_id, field_ra, field_dec = ZTF_field['id'], \
                                        ZTF_field['ra'], \
                                        ZTF_field['dec']
        ZTF_CCD_corners = load_ZTF_CCD_corners(field_id, field_ra, field_dec)
        if test_within_CCD_corners(ra, dec, ZTF_CCD_corners):
            fields.append(ZTF_field['id'])

    return fields


def test_within_RCID_corners(ra, dec, ZTF_RCID_corners_single):
    lower_right = ZTF_RCID_corners_single[3]
    lower_left = ZTF_RCID_corners_single[2]
    upper_right = ZTF_RCID_corners_single[0]
    upper_left = ZTF_RCID_corners_single[1]

    polygon = Polygon([lower_right,
                       lower_left,
                       upper_left,
                       upper_right])
    point = Point(ra, dec)
    return polygon.contains(point)


def return_rcid(field_id, ra, dec):
    ZTF_RCID_corners = return_ZTF_RCID_corners(field_id)

    for rcid in range(64):
        ZTF_RCID_corners_single = ZTF_RCID_corners[rcid]
        if test_within_RCID_corners(ra, dec, ZTF_RCID_corners_single):
            return rcid

    print('No matching rcid found')
    return None
