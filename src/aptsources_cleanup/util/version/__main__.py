# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals
from .._3to2 import *
import sys
from . import version_info


if len(sys.argv) > 1:
	version = sys.argv[1]
else:
	version = input()

version_info.from_repo(version)._print_data_module()
