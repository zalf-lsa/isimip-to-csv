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

LOCAL_RUN = True

def main():

    config = {
        "path_to_data": "m:/data/climate/isimip/grids/daily/" if LOCAL_RUN else "/archiv-daten/md/data/climate/isimip/grids/daily/",
        #"path_to_output": "m:/data/climate/dwd/csvs/germany/" if LOCAL_RUN else "/archiv-daten/md/data/climate/dwd/csvs/germany/",
        "path_to_output": "g:/csvs/earth/" if LOCAL_RUN else "/archiv-daten/md/data/climate/isimip/csvs/earth/",
        "start-y": 1,
        "end-y": -1,
        "start-year": 1971,
        "end-year": 2005,
        "start-month": 1,
        "end-month": 12
    }
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            kkk, vvv = arg.split("=")
            if kkk in config:
                config[kkk] = int(vvv)

    elem_to_varname = {
        "tmin": {"prefix": "tasmin_bced_1960_1999", "var": "tasminAdjust", "folder": "tmin/"},
        "tavg": {"prefix": "tas_bced_1960_1999", "var": "tasAdjust", "folder": "tavg/"},
        "tmax": {"prefix": "tasmax_bced_1960_1999", "var": "tasmaxAdjust", "folder": "tmax/"},
        "precip": {"prefix": "pr_bced_1960_1999", "var": "prAdjust", "folder": "precip/"},
        "relhumid": {"prefix": "hurs", "var": "hurs", "folder": "relhumid/"},
        "globrad": {"prefix": "rsds_bced_1960_1999", "var": "rsdsAdjust", "folder": "short_rad/"},
        "wind": {"prefix": "wind_bced_1960_1999", "var": "windAdjust", "folder": "wind/"}
    }

    files = defaultdict(lambda: defaultdict(dict))
    for start_year in range(1971, 2005, 10):
        for elem, dic in elem_to_varname.iteritems():
            end_year = start_year + (9 if start_year < 2001 else 4)
            files[(start_year, end_year)][elem] = config["path_to_data"] + dic["folder"] + dic["prefix"] + "_ipsl-cm5a-lr_hist_" + str(start_year) + "-" + str(end_year) + ".nc"


    def write_files(cache):
        no_of_files = len(cache)
        count = 0
        for (y, x), rows in cache.iteritems():
            path_to_outdir = config["path_to_output"] + "row-" + str(y) + "/"
            if not os.path.isdir(path_to_outdir):
                os.makedirs(path_to_outdir)

            path_to_outfile = path_to_outdir + "col-" + str(x) + ".csv"
            if not os.path.isfile(path_to_outfile):
                with open(path_to_outfile, "wb") as _:
                    writer = csv.writer(_, delimiter=",")
                    writer.writerow(["iso-date", "tmin", "tavg", "tmax", "precip", "relhumid", "globrad", "windspeed"])
                    writer.writerow(["[]", "[°C]", "[°C]", "[°C]", "[mm]", "[%]", "[MJ m-2]", "[m s-1]"])

            with open(path_to_outfile, "ab") as _:
                writer = csv.writer(_, delimiter=",")
                for row in rows:
                    writer.writerow(row)

            count = count + 1
            if count % 1000 == 0:
                print count, "/", no_of_files, "written"


    write_files_threshold = 50 #ys

    for (start_year, end_year), elem_to_file in files.iteritems():
        datasets = {}
        for elem, filepath in elem_to_file.iteritems():
            datasets[elem] = Dataset(filepath) 

        sum_days = 0
        for year in range(start_year, end_year + 1):

            start_year = time.clock()
            days_in_year = date(year, 12, 31).timetuple().tm_yday

            if year < config["start-year"]:
                sum_days = sum_days + days_in_year
                continue
            if year > config["end-year"]:
                break

            print "year:", year, "sum-days:", sum_days, "ys ->",

            days_per_loop = 31
            for doy_i in range(date(year, config["start-month"], 1).timetuple().tm_yday - 1, days_in_year, days_per_loop):

                if (date(year, config["end-month"] + 1, 1).timetuple().tm_yday - 1 if config["end-month"] < 12 else date(year, 12, 31).timetuple().tm_yday) <= doy_i:
                    break

                end_i = doy_i + days_per_loop if doy_i + days_per_loop < days_in_year else days_in_year
                data = {}
                for elem, ds in datasets.iteritems():
                    data[elem] = np.copy(ds.variables[elem_to_varname[elem]["var"]][sum_days + doy_i : end_i])

                ref_data = data["tavg"]
                no_of_days = ref_data.shape[0]
                cache = defaultdict(list)

                for y in range(config["start-y"] - 1, ref_data.shape[1] if config["end-y"] < 0 else config["end-y"]):
                    for x in range(ref_data.shape[2]):

                        if int(ref_data[0, y, x]) > 1.0E19:
                            continue

                        for i in range(no_of_days):
                            row = [
                                (date(year, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d"),
                                str(round(data["tmin"][i, y, x] - 273.15, 2)),
                                str(round(data["tavg"][i, y, x] - 273.15, 2)),
                                str(round(data["tmax"][i, y, x] - 273.15, 2)),
                                str(round(data["precip"][i, y, x] * 60 * 60 * 24, 2)),
                                str(round(data["relhumid"][i, y, x], 2)),
                                str(round(data["globrad"][i, y, x] * 60 * 60 * 24 / 1000000, 4)),
                                str(round(data["wind"][i, y, x], 2))
                            ]
                            cache[(y,x)].append(row)

                    print y, #str(y) + "|" + str(int(end_y - start_y)) + "s ",

                    if y > config["start-y"] and y % write_files_threshold == 0:
                        print ""
                        s = time.clock()
                        write_files(cache)
                        cache = defaultdict(list)
                        e = time.clock()
                        print "wrote", write_files_threshold, "ys in", (e-s), "seconds"

                print ""

                #write remaining cache items
                write_files(cache)

                end_year = time.clock()
                print "running year", year, "took", (end_year - start_year), "seconds"

            sum_days = sum_days + days_in_year

        for _ in datasets.values():
            _.close()

main()