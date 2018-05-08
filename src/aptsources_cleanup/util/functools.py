from __future__ import print_function, division, absolute_import, unicode_literals
from ._3to2 import *
from functools import *
from .operator import rapply, identity

__all__ = (
	'comp', 'cmp_to_key', 'total_ordering', 'reduce', 'update_wrapper', 'wraps',
	'partial'
)


def comp(*funcs):
	if len(funcs) <= 1:
		return funcs[0] if funcs else identity
	return partial(reduce, rapply, funcs)
