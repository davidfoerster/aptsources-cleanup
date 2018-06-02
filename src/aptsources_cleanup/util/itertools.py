# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ('filterfalse', 'accumulate', 'foreach', 'unique', 'count')

from ._3to2 import *
from .operator import identity


try:
	from itertools import filterfalse, accumulate
except ImportError:
	from itertools import ifilterfalse as filterfalse
	from .impl.itertools import *


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
			yield v
			seen_add(k)


def count(iterable):
	"""Simply returns the number of entries (left) in the given iterable."""
	return sum(1 for _ in iterable)


def last(iterable, *default):
	"""Return the last item of an iterable or 'default' if there's none."""
	assert len(default) <= 1
	iterable = iter(iterable)

	try:
		x = next(iterable)
	except StopIteration:
		if default:
			return default[0]
		raise

	for x in iterable:
		pass
	return x
