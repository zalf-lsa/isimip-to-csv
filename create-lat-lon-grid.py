#!/usr/bin/python
# -*- coding: UTF-8

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/. */

# Authors:
# Michael Berg-Mohnicke <michael.berg@zalf.de>
#
# Maintainers:
# Currently maintained by the authors.
#
# This file has been created at the Institute of
# Landscape Systems Analysis at the ZALF.
# Copyright (C: Leibniz Centre for Agricultural Landscape Research (ZALF)

import time
import os
import math
import json
import csv
import itertools
#import copy
from StringIO import StringIO
from datetime import date, datetime, timedelta
from collections import defaultdict, OrderedDict
#import types
import sys
print sys.path
#import zmq
#print "pyzmq version: ", zmq.pyzmq_version(), " zmq version: ", zmq.zmq_version()

from netCDF4 import Dataset
import numpy as np

def main():

    config = {
        "path-to-data": "C:/Users/berg.ZALF-AD/Desktop/"
    }
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            kkk, vvv = arg.split("=")
            if kkk in config:
                config[kkk] = vvv

    ds = Dataset(config["path-to-data"] + "tas_bced_1960_1999_ipsl-cm5a-lr_hist_1971-1980.nc")
    lats = np.copy(ds.variables["lat"])
    lons = np.copy(ds.variables["lon"])
    temps = np.copy(ds.variables["tasAdjust"][0])

    lat_lon_grid_file = open("lat-lon.grid", "w")
    data_no_data_grid_file = open("data-no-data.grid", "w")
    latlon_to_rowcol_json_file = open("latlon-to-rowcol.json", "w")
    rowcol_to_latlon_json_file = open("rowcol-to-latlon.json", "w")

    lat_lon_grid_file.write("ncols 720\nnrows 360\nnodata_value --------------\n")
    data_no_data_grid_file.write("ncols 720\nnrows 360\nnodata_value -\n")
    ll_to_rc_json_data = []
    rc_to_ll_json_data = []
  
    for row in range(0, 360):
        ll_line = []
        dnd_line = []
        for col in range(0, 720):
            lat = round(lats[row], 2)
            lon = round(lons[col], 2)

            is_data = temps[row, col] > -1000 and temps[row, col] < 1000
            dnd_line.append("x" if is_data else "-")
            if is_data:
                ll_to_rc_json_data.append([[lat, lon], [row, col]])
                rc_to_ll_json_data.append([[row, col], [lat, lon]])
                ll_line.append("{:+06.2f}|{:+07.2f}".format(lat, lon))
            else:
                ll_line.append("--------------")

        lat_lon_grid_file.write(" ".join(ll_line))
        data_no_data_grid_file.write(" ".join(dnd_line))
        if row < 359:
            lat_lon_grid_file.write("\n")
            data_no_data_grid_file.write("\n")

        if row % 10 == 0:
            print "wrote line", row
    
    json.dump(ll_to_rc_json_data, latlon_to_rowcol_json_file)#, indent=2)
    json.dump(rc_to_ll_json_data, rowcol_to_latlon_json_file)#, indent=2)

    lat_lon_grid_file.close()
    data_no_data_grid_file.close()
    latlon_to_rowcol_json_file.close()
    rowcol_to_latlon_json_file.close()
    ds.close()

main()