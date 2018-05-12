# -*- coding: utf-8
from __future__ import absolute_import, unicode_literals

__all__ = ('ChainMap',)

from .._3to2 import *
from ..operator import methodcaller
import operator


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
