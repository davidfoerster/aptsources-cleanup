# -*- coding: utf-8
from __future__ import absolute_import, unicode_literals

__all__ = ('ChainMap',)

from .._3to2 import *
from ..operator import methodcaller
import operator
import itertools
import functools


class ChainMap(object):
	"""A minimal implementation of a chained map
	that is compatible with Python 3's collections.ChainMap.
	"""

	__slots__ = ('_data',)

	_missing_key_marker = object()

	_is_not_missing_key_marker = (
		functools.partial(operator.is_not, _missing_key_marker))


	def __init__(self, *underlying):
		super(ChainMap, self).__init__()
		self._data = underlying


	def __bool__(self):
		return any(self._data)


	def __contains__(self, key):
		return any(map(methodcaller(operator.contains, key), self._data))


	def __getitem__(self, key):
		value = self.get(key, self._missing_key_marker)
		if value is self._missing_key_marker:
			raise KeyError
		return value


	def get(self, key, default_value=None):
		return next(
			filter(self._is_not_missing_key_marker,
				map(methodcaller('get', key, self._missing_key_marker), self._data)),
			default_value)


	def keyiter(self):
		return itertools.chain(*self._data)


	def valueiter(self):
		return itertools.chain(*map(methodcaller('values'), self._data))


	def itemiter(self, reverse=False):
		return itertools.chain(*map(methodcaller('items'),
			reversed(self._data) if reverse else self._data))


	def copy(self):
		return dict(self.itemiter(True))


	def __repr__(self):
		return 'collections.{:s}({:s})'.format(
			type(self).__name__, ', '.join(map(repr, self._data)))
