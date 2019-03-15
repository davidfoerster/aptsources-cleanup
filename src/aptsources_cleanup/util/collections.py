# -*- coding: utf-8
"""Like the eponymous built-in module but with additional back-ported
functonality if any.
"""

__all__ = ['ExtSet']

from collections import *
import collections as _collections
__all__ += _collections.__all__


class ExtSet(set):

	def add(self, x):
		l = len(self)
		super().add(x)
		return l != len(self)
