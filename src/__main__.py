#!/usr/bin/python3 -OEs
# -*- coding: utf-8

import sys
from pathlib import PurePath
sys.path = [ p for p in sys.path if "site-packages" not in PurePath(p).parts ]

import runpy
runpy.run_module('aptsources_cleanup', run_name='__main__')
