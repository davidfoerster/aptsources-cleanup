from __future__ import print_function, division, absolute_import, unicode_literals
from ._3to2 import *
import functools as _functools
from functools import *
from .operator import rapply, identity

__all__ = ('comp',) + tuple(_functools.__all__)


def comp(*funcs):
	if len(funcs) <= 1:
		return funcs[0] if funcs else identity
	return partial(reduce, rapply, funcs)
