from __future__ import \
	print_function, division, absolute_import, unicode_literals
from ._3to2 import *
import operator
import collections as _collections
from collections import *
from itertools import islice
from .operator import methodcaller

__all__ = _collections.__all__


try:
	ChainMap

except NameError:
	class ChainMap(object):

		def __init__(self, *underlying):
			self._data = underlying or ({},)


		def _filter_maps_with_key(self, key):
			return filter(methodcaller(operator.contains, key), self._data)


		def __getitem__(self, key):
			try:
				return next(iter(self._filter_maps_with_key(key)))[key]
			except StopIteration:
				raise KeyError


		def get(self, key, default_value=None):
			try:
				return next(iter(self._filter_maps_with_key(key)))[key]
			except StopIteration:
				return default_value
