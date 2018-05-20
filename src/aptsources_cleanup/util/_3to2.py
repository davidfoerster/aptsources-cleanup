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
	basestring = (str, bytes)
else:
	from .impl.input import input
	__all__.extend(('str', 'bytes', 'range', 'input'))


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
