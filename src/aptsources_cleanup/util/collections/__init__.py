# -*- coding: utf-8
"""Like the eponymous built-in module but with additional back-ported
functonality if any.
"""

__all__ = ['ExtSet']

from collections import *

import collections as _collections
__all__ += _collections.__all__


class ExtSet(set):
	"""Some extensions to the built-in set class"""

	__slots__ = ()


	def add(self, x):
		"""Same as set.add(). Returns True if the set was changed."""

		l = len(self)
		super().add(x)
		return l != len(self)


	def discard(self, x):
		"""Same as set.discard(). Returns True if the set was changed."""

		l = len(self)
		super().discard(x)
		return l != len(self)


	def discard_first_of(self, iterable, default=None):
		"""Removes and returns the first element that is a member of this set.

		Elements are drawn from an iterable. If none of them is a member of this
		set, the default value is returned instead.
		"""

		return next(filter(self.discard, iterable), default)
