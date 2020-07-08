# -*- coding: utf-8
from os import __all__
from os import *

import collections.abc


if "fspath" not in globals():
	def fspath(path, *, _string_types=(str, collections.abc.ByteString)):
		if not isinstance(path, _string_types):
			try:
				path = path.__fspath__()
			except AttributeError:
				raise TypeError("Not a path-like type: " + str(type(path))) from None
		return path
