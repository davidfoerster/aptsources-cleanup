# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ('filterfalse', 'accumulate', 'foreach', 'unique', 'count')

from ._3to2 import *
from .functools import comp
from .collections import ExtSet


try:
	from itertools import filterfalse, accumulate
except ImportError:
	from itertools import ifilterfalse as filterfalse
	from .impl.itertools import *


def foreach(func, *iterables):
	"""Call 'func' on each item in 'iterable'."""

	if len(iterables) > 1:
		for x in zip(*iterables):
			func(*x)
	else:
		for x in iterables[0]:
			func(x)


def unique(iterable, key=None):
	"""Removes/skips all duplicate entries after their first occurrence."""

	not_seen = ExtSet().add
	if key is not None:
		not_seen = comp(key, not_seen)
	return filter(not_seen, iterable)


def count(iterable):
	"""Simply returns the number of entries (left) in the given iterable."""
	return sum(1 for _ in iterable)


def last(iterable, *default):
	"""Return the last item of an iterable or 'default' if there's none."""
	assert len(default) <= 1

	try:
		iterable = reversed(iterable)
	except TypeError:
		pass
	else:
		return next(iterable, *default)

	for x in iterable:
		pass

	try:
		return x
	except UnboundLocalError:
		pass

	if not default:
		raise StopIteration
	return default[0]
