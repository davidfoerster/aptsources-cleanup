# -*- coding: utf-8
"""String utilities"""

__all__ = (
	"startswith_token", "prefix", "strip", "lstrip", "rstrip",
	"contains_ordered"
)

import operator

if __debug__:
	import collections
	from warnings import warn
	from .itertools import map_pairs


def startswith_token(s, prefix, separators=None):
	"""Tests if a string is either equal to a given prefix or prefixed by it
	followed by a separator.
	"""

	if separators is None:
		return s == prefix

	prefix_len = len(prefix)

	if s.startswith(prefix):
		if len(s) == prefix_len:
			return True

		if isinstance(separators, str):
			sep = separators
			return s.find(sep, prefix_len) >= 0

		for sep in separators:
			if s.find(sep, prefix_len) >= 0:
				return True

	return False


def prefix(s, *prefixes, reverse=False):
	if reverse:
		pos = s.rfind(*prefixes)
	else:
		pos = s.find(*prefixes)
	return s[:pos] if pos >= 0 else s


def strip(s, xfixes, *, start=None, stop=None):
	return _strip_impl("lr", s, xfixes, start, stop)

def lstrip(s, prefixes, *, start=None, stop=None):
	return _strip_impl("l", s, xfixes, start, stop)

def rstrip(s, suffixes, *, start=None, stop=None):
	return _strip_impl("r", s, xfixes, start, stop)


def _strip_impl(mode, s, xfixes, start, stop):
	assert mode and not mode.strip("lr")
	len_s = len(s)
	start = _normalize_index(start, 0, len_s)
	stop  = _normalize_index(stop, len_s, len_s)
	xfixes = _strip_prepare_xfixes(xfixes, mode)

	if "l" in mode:
		start = _lstrip_start(s, start, stop, xfixes)
	if "r" in mode:
		stop = _rstrip_stop(s, start, stop, xfixes)

	return s[ start : stop ]


def _normalize_index(idx, default, sequence_len):
	if idx is None:
		idx = default
	elif idx < 0:
		idx += sequence_len
		if idx < 0:
			raise IndexError(format(idx - sequence_len, "d"))

	return idx


def _strip_prepare_xfixes(xfixes, mode):
	if isinstance(xfixes, str):
		return (xfixes,)

	if __debug__:
		assert isinstance(xfixes, collections.abc.Sized)

		if "l" in mode and any(
			map_pairs(str.startswith, sorted(xfixes, reverse=True))
		):
			warn("not prefix-free", UserWarning)

		if "r" in mode and any(
			map_pairs(str.startswith, sorted(
				map(operator.itemgetter(slice(None, None, -1)), xfixes), reverse=True))
		):
			warn("not suffix-free", UserWarning)

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
	if reverse:
		offset = len(s)
		find = _contains_ordered_rfind
		advance = operator.sub
	else:
		offset = 0
		find = str.find
		advance = operator.add

	for infix in infixes:
		offset = find(s, infix, offset)
		if offset < 0:
			return False
		offset = advance(offset, len(infix))
	return True


def _contains_ordered_rfind(s, infix, offset):
	return s.rfind(infix, 0, max(offset, 0))
