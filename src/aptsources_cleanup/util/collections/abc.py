# -*- coding: utf-8
"""Like the eponymous built-in module but with additional back-ported
functonality if any.
"""

__all__ = []

from collections.abc import *
from collections import abc as _abc
__all__ += _abc.__all__


try:
	from _collections_abc import _check_methods
except ImportError:
	def _check_methods(C, *methods):
		mro = C.__mro__
		for method in methods:
			for B in mro:
				if method in B.__dict__:
					if B.__dict__[method] is None:
						return NotImplemented
					break
			else:
				return NotImplemented
		return True


if "Collection" not in locals():
	__all__.append("Collection")

	class Collection(Sized, Iterable, Container):

		__slots__ = ()

		@classmethod
		def __subclasshook__(cls, C):
			if cls is not Collection:
				return NotImplemented
			return _check_methods(C,  "__len__", "__iter__", "__contains__")

	Collection.register(Set)
	Collection.register(Sequence)
	Collection.register(Mapping)
