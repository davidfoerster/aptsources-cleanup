# -*- coding: utf-8
"""Genreate the content of a ._data module for use witht this package"""
from __future__ import print_function, division, absolute_import, unicode_literals
from .._3to2 import *
import sys, locale
from . import version_info


locale.setlocale(locale.LC_ALL, '')

if len(sys.argv) > 1:
	version = sys.argv[1]
else:
	version = input()

output = sys.stdout
if not output.encoding:
	import codecs
	encoding = locale.getpreferredencoding()
	output = codecs.getwriter(encoding)(output)
	output.encoding = encoding

with output:
	version_info.from_repo(version)._print_data_module(output)
