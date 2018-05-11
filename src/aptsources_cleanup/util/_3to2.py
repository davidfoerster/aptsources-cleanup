# -*- coding: utf-8
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
