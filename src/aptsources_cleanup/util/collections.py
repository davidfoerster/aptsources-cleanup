# -*- coding: utf-8
"""Like the eponymous built-in module but with additional back-ported
functonality if any.
"""

__all__ = ['ExtSet']

from collections import *
from collections import abc

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
