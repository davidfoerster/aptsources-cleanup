# -*- coding: utf-8
"""Helpers for code that tries to support both Python 2.7 and 3+

such as imports under new names or reimplementations of built-in functions that
behave differently.
"""
from __future__ import print_function, division, absolute_import

__all__ = ['nativestr', 'basestring', 'TypesType']

nativestr = str


try:
	from __builtin__ import \
		unicode as str, str as bytes, basestring, raw_input, \
		xrange as range

except ImportError:
	from builtins import input
	basestring = (str, bytes)

else:
	__all__.extend(('str', 'bytes', 'range', 'input'))

	import sys, locale

	def input(prompt=None):
		"""Wraps 'raw_input' and encodes its return value

		Using the encoding of sys.stdin if available, or the preferred encoding of
		the current locale.
		"""

		answer = raw_input() if prompt is None else raw_input(prompt)
		return str(answer, sys.stdin.encoding or locale.getpreferredencoding())


try:
	from future_builtins import *
except ImportError:
	pass
else:
	__all__.extend(('ascii', 'filter', 'hex', 'map', 'oct', 'zip'))


try:
	from types import ClassType as TypesType
except ImportError:
	TypesType = type
else:
	TypesType = (type, TypesType)
