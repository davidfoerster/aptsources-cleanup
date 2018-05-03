#!/usr/bin/python3 -OEs
import sys
sys.path[:] = [p for p in sys.path if 'site-packages' not in p]

import runpy
#_magic = '@@aptsources-cleanup@@'
runpy.run_module('aptsources_cleanup')
