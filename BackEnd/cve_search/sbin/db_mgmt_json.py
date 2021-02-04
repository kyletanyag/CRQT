#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Manager for the database for the NVD JSON Files
#
# Current import is mapping all the old XML scheme from the NVD JSON files (WiP)
#
#
# Software is free software released under the "GNU Affero General Public License v3.0"
#
# Copyright (c) 2019 	Alexandre Dulaunoy - a@foo.be

# Imports
# make sure these modules are available on your system
import argparse
import os
import sys

runPath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(runPath, ".."))

from lib.Sources_process import CVEDownloads
from lib.DatabaseLayer import getSize


# parse command line arguments
argparser = argparse.ArgumentParser(
    description="populate/update the local CVE database"
)
argparser.add_argument("-u", action="store_true", help="update the database")
argparser.add_argument("-p", action="store_true", help="populate the database")
argparser.add_argument(
    "-a", action="store_true", default=False, help="force populating the CVE database"
)
argparser.add_argument(
    "-f", action="store_true", default=False, help="force update of the CVE database"
)
argparser.add_argument("-v", action="store_true", help="verbose output")
args = argparser.parse_args()


if __name__ == "__main__":
    cvd = CVEDownloads()

    cvd.logger.debug("{}".format(" ".join(sys.argv)))

    if args.u:

        last_modified = cvd.update()

    elif args.p:
        c = getSize(cvd.feed_type.lower())
        if args.v:
            cvd.logger.info(str(c))
        if c > 0 and args.a is False:
            cvd.logger.info("database already populated")
        else:
            last_modified = cvd.populate()
