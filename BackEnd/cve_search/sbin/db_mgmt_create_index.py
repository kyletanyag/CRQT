#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Script to check and ensure that the recommended index are created as recommended.
#
# Software is free software released under the "GNU Affero General Public License v3.0"
#
# Copyright (c) 2014       psychedelys
# Copyright (c) 2015-2018  Pieter-Jan Moreels - pieterjan.moreels@gmail.com
# Imports
import logging
import os
import sys

runPath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(runPath, ".."))

from lib.Sources_process import DatabaseIndexer
from lib.LogHandler import UpdateHandler


logging.setLoggerClass(UpdateHandler)


if __name__ == '__main__':
    di = DatabaseIndexer()

    di.create_indexes()
