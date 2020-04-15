# -*- coding: utf-8

__all__ = ('filterfalse', 'accumulate', 'foreach', 'unique', 'count')

from .functools import comp
from .collections import ExtSet
from itertools import filterfalse, accumulate


def foreach(func, iterable0, *iterables, star_call=False):
	"""Call 'func' on each item in 'iterable'."""

	if iterables:
		if star_call:
			raise TypeError("Cannot use star_call with multiple iterables")
		iterable0 = zip(iterable0, *iterables)
		star_call = True

	if star_call:
		for x in iterable0:
			func(*x)
	else:
		for x in iterable0:
			func(x)


def unique(iterable, key=None):
	"""Removes/skips all duplicate entries after their first occurrence."""

	not_seen = ExtSet().add
	if key is not None:
		not_seen = comp(key, not_seen)
	return filter(not_seen, iterable)


def count(iterable):
	"""Simply returns the number of entries (left) in the given iterable."""

	try:
		return len(iterable)
	except TypeError:
		pass
	return sum(1 for _ in iterable)


def last(iterable, *default):
	"""Return the last item of an iterable or 'default' if there's none."""

	try:
		iterable = reversed(iterable)
	except TypeError:
		pass
	else:
		return next(iterable, *default)

	iterable = iter(iterable)
	x = next(iterable, *default)
	for x in iterable:
		pass
	return x
