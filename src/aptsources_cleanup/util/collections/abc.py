# -*- coding: utf-8
"""Like the eponymous built-in module but with additional back-ported
functonality if any.
"""

__all__ = []

from collections.abc import *
from _collections_abc import _check_methods
from collections import abc as _abc
__all__ += _abc.__all__


if "Collection" not in locals():
	__all__.append("Collection")

	class Collection(Sized, Iterable, Container):

		__slots__ = ()

		@classmethod
		def __subclasshook__(cls, C):
			if cls is not Collection:
				return NotImplemented
			return _check_methods(C,  "__len__", "__iter__", "__contains__")

