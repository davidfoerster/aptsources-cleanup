#!/usr/bin/env python3
# -*- coding: utf-8

"""Returns the paths of the files behind the given modules."""

from __future__ import absolute_import, print_function
import sys, operator, importlib

try:
	from future_builtins import *
except ImportError:
	pass


if __name__ == "__main__":
	print(
		*map(operator.attrgetter("__file__"),
			map(importlib.import_module, sys.argv[1:])),
		sep="\n")
