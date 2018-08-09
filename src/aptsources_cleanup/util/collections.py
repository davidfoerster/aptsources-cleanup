# -*- coding: utf-8
"""Like the eponymous built-in module but with additional back-ported
functonality if any.
"""
from __future__ import absolute_import
from collections import *

import collections as _collections
__all__ = _collections.__all__


try:
	ChainMap
except NameError:
	from .impl.chainmap import ChainMap


class ExtSet(set):

	def add(self, x):
		l = len(self)
		super(ExtSet, self).add(x)
		return l != len(self)
