#!/usr/bin/python3 -OEs
# -*- coding: utf-8

import sys
sys.path[:] = [p for p in sys.path if 'site-packages' not in p.split('/')]

import runpy
runpy.run_module('aptsources_cleanup', run_name='__main__')
