# -*- coding: utf-8
from __future__ import division, absolute_import, unicode_literals

__all__ = ('timezone',)

from .._3to2 import *
from datetime import *


DELTA_ZERO = timedelta()


class timezone(tzinfo):
	"""A minimal reimplementaion of Python 3's timezone class"""

	__slots__ = ('_offset', '_name')


	def __init__(self, offset, name=None):
		if not isinstance(offset, timedelta):
			raise TypeError(
				'offset: expected timedelta, got ' + type(offset).__name__)
		if not (name is None or isinstance(name, basestring)):
			raise TypeError('name')

		super(timezone, self).__init__()
		self._offset = offset
		self._name = name

		if abs(self._utcoffset_seconds()) > 12 * 3600:
			raise ValueError('offset too large: ' + str(offset))


	def _utcoffset_seconds(self):
		return self._offset.days * (24 * 3600) + self._offset.seconds


	def utcoffset(self, dt=None):
		return self._offset


	def tzname(self, dt=None):
		return self._name


	def dst(self, dt=None):
		return DELTA_ZERO


	def __str__(self):
		minutes = self._utcoffset_seconds() // 60
		return '{:s}{:02d}{:02d}'.format(
			('+', '-')[minutes < 0], *divmod(abs(minutes), 60))


	def __repr__(self):
		return 'datetime.{:s}({!r}, {!r})'.format(
			type(self).__name__, self._offset, self._name)
