# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ('filterfalse', 'foreach', 'unique', 'count')

from ._3to2 import *
from .operator import identity


try:
	from itertools import filterfalse
except ImportError:
	from itertools import ifilterfalse as filterfalse


def foreach(func, iterable):
	"""Call 'func' on each item in 'iterable'."""

	for x in iterable:
		func(x)


def unique(iterable, key=None):
	"""Removes/skips all duplicate entries after their first occurrence."""

	if key is None:
		key = identity

	seen = set()
	seen_add = seen.add
	for v in iterable:
		k = key(v)
		if k not in seen:
			seen_add(k)
			yield v


def count(iterable):
	"""Simply returns the number of entries (left) in the given iterable."""
	return sum(1 for _ in iterable)
