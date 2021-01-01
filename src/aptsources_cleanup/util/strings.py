# -*- coding: utf-8
"""String utilities"""

__all__ = (
	"startswith_token", "prefix", "rprefix", "strip", "lstrip", "rstrip",
	"contains_ordered"
)

import operator
import collections
import collections.abc

if __debug__:
	from warnings import warn
	from .itertools import map_pairs


StringTypes = (str, collections.UserString, collections.abc.ByteString)


def startswith_token(s, prefix, separators=None):
	"""Tests if a string is either equal to a given prefix or prefixed by it
	followed by a separator.
	"""

	if separators is None:
		return s == prefix
	return (
		s.startswith(prefix) and
		(len(s) == len(prefix) or s.startswith(separators, len(prefix))))


def prefix(s, sep):
	"""Returns the prefix of s delimited by a separator.

	sep may be a collection in which case the separator with the least position
	in s is used.

	If none of the separators occurs in s, s itself is returned.
	"""

	limit = None
	for sep in _prepare_xfixes(sep, 1):
		pos = s.find(sep, 0, limit and (limit + len(sep) - 1))
		if pos >= 0:
			limit = pos
			if not limit:
				break

	return s[:limit]


def rprefix(s, sep):
	"""Returns the prefix of s delimited by a separator looking from the back.

	sep may be a collection in which case the separator with the greatest position
	in s is used.

	If none of the separators occurs in s, s itself is returned.
	"""

	offset = None
	limit = None
	for sep in _prepare_xfixes(sep, 2):
		pos = s.rfind(sep, limit and max(limit - len(sep) + 1, 0))
		if pos >= 0:
			offset = pos
			limit = pos + len(sep)

	return s[:offset]


def strip(s, xfixes, *, start=None, stop=None):
	return _strip_impl(3, s, xfixes, start, stop)

def lstrip(s, prefixes, *, start=None, stop=None):
	return _strip_impl(1, s, xfixes, start, stop)

def rstrip(s, suffixes, *, start=None, stop=None):
	return _strip_impl(2, s, xfixes, start, stop)


def _strip_impl(mode, s, xfixes, start, stop):
	assert 0 < mode <= 3
	len_s = len(s)
	start = _normalize_index(start, 0, len_s)
	stop  = _normalize_index(stop, len_s, len_s)
	xfixes = _prepare_xfixes(xfixes, mode)

	if mode & 1:
		start = _lstrip_start(s, start, stop, xfixes)
	if mode & 2:
		stop = _rstrip_stop(s, start, stop, xfixes)

	return s[ start : stop ]


def _normalize_index(idx, default, sequence_len):
	if idx is None:
		return default
	if idx >= 0:
		return min(idx, sequence_len)
	return max(idx + sequence_len, 0)


def _prepare_xfixes(xfixes, mode):
	if isinstance(xfixes, StringTypes):
		return (xfixes,)

	if __debug__:
		for mode_name, mode_flag, slice_step in (
			("prefix", 1, 1), ("suffix", 2, -1)
		):
			if (mode & mode_flag and
				any(map_pairs(
					lambda a, b: b.startswith(a),
					sorted(
						map(operator.itemgetter(slice(None, None, slice_step)), xfixes))))
			):
				warn(
					"Not {:s}-free; results may be ambiguous: {!r}".format(
						mode_name, xfixes),
					UserWarning)

	return xfixes


def _lstrip_start(s, start, stop, prefixes):
	assert start >= 0
	while start < stop:
		for prefix in prefixes:
			step = start + len(prefix)
			if start < step <= stop and s.find(prefix, start, step) >= 0:
				start = step
				break
		else:
			break
	return start


def _rstrip_stop(s, start, stop, suffixes):
	assert start >= 0
	while start < stop:
		for suffix in suffixes:
			step = stop - len(suffix)
			if start <= step < stop and s.find(suffix, step, stop) >= 0:
				stop = step
				break
		else:
			break
	return stop


def contains_ordered(s, infixes, *, reverse=False):
	limit = None

	if reverse:
		for infix in infixes:
			limit = s.rfind(infix, 0, limit)
			if limit < 0:
				return False
	else:
		for infix in infixes:
			limit = s.find(infix, limit)
			if limit < 0:
				return False
			limit += len(infix)

	return True
