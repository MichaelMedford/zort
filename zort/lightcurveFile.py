#! /usr/bin/env python
"""
lightcurveFile.py
ZTF objects are stored in lightcurve files. This class allows for
iteration through a lightcurve file in order to inspect each object's
lightcurve. Filters can be applied to objects and/or lightcurves.
"""

import os
from zort.object import Object


################################
#                              #
#  LightcurveFile Class        #
#                              #
################################

class LightcurveFile:
    """
    ZTF objects are stored in lightcurve files. This class allows for
    iteration through a lightcurve file in order to inspect each object's
    lightcurve. Filters can be applied to objects and/or lightcurves.
    """

    def __init__(self, filename,
                 nepochs_cut=None,
                 filterid_filter=None,
                 fieldid_filter=None,
                 rcid_filter=None):
        self.filename = self._set_filename(filename)
        self.objects_filename = self.return_objects_filename()
        self.objects_file = self.return_objects_file()
        self.nepochs_cut = self._set_filter(nepochs_cut)
        self.filterid_filter = self._set_filter(filterid_filter)
        self.fieldid_filter = self._set_filter(fieldid_filter)
        self.rcid_filter = self._set_filter(rcid_filter)

    def __iter__(self):
        return self

    def __next__(self):
        line = self.objects_file.readline()
        if int(self._return_parsed_line(line)[-1]) >= 11028:
            raise StopIteration
        if self.apply_filter(line):
            return self.return_object(line)
        else:
            return None

    def __exit__(self):
        self.objects_file.close()

    def _set_filter(self, filter):
        if filter is None:
            return None
        else:
            return int(filter)

    def _return_parsed_line(self, line):
        return line.replace('\n', '').split(',')

    def _set_filename(self, filename):
        try:
            filename = filename.decode()
        except AttributeError:
            filename = filename

        if '/' not in filename:
            filename = os.getenv('ZTF_LC_DATA') + '/' + filename

        return filename

    def return_object(self, line):
        buffer_position = self._return_parsed_line(line)[-1]
        return Object(self.filename, buffer_position)

    def return_objects_file(self):
        file = open(self.objects_filename, 'r')
        _ = file.readline()
        return file

    def return_objects_filename(self):
        objects_filename = self.filename.replace('.txt', '.objects')
        return objects_filename

    def apply_filter(self, line):

        if self.nepochs_cut is not None:
            nepochs = int(self._return_parsed_line(line)[1])
            if nepochs < self.nepochs_cut:
                return False

        if self.filterid_filter is not None:
            filterid = int(self._return_parsed_line(line)[2])
            if filterid != self.filterid_filter:
                return False

        if self.fieldid_filter is not None:
            fieldid = int(self._return_parsed_line(line)[3])
            if fieldid != self.fieldid_filter:
                return False

        if self.rcid_filter is not None:
            rcid = int(self._return_parsed_line(line)[4])
            if rcid != self.rcid_filter:
                return False

        return True
