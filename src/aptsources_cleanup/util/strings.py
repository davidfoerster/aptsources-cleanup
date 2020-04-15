# -*- coding: utf-8
"""String utilities"""

__all__ = (
	"startswith_token", "prefix", "strip", "lstrip", "rstrip",
	"contains_ordered"
)

import operator


def startswith_token(s, prefix, sep=None):
	"""Tests if a string is either equal to a given prefix or prefixed by it
	followed by a separator.
	"""

	if sep is None:
		return s == prefix

	prefix_len = len(prefix)
	return s.startswith(prefix) and (
		not sep or len(s) == prefix_len or
		s.find(sep, prefix_len, prefix_len + len(sep)) == prefix_len)


def prefix(s, *prefixes, reverse=False):
	if reverse:
		pos = s.rfind(*prefixes)
	else:
		pos = s.find(*prefixes)
	return s[:pos] if pos >= 0 else s


def strip(s, xfixes):
	xfixes = _strip_prepare_xfixes(xfixes)
	stop = len(s)
	start = _lstrip_start(s, 0, stop, xfixes)
	stop = _rstrip_stop(s, start, stop, xfixes)
	return s[start:stop]


def lstrip(s, prefixes):
	return s[_lstrip_start(s, 0, len(s), _strip_prepare_xfixes(prefixes)):]


def rstrip(s, suffixes):
	return s[:_rstrip_stop(s, 0, len(s), _strip_prepare_xfixes(suffixes))]


def _strip_prepare_xfixes(xfixes):
	if isinstance(xfixes, str):
		return (xfixes,)

	it_xfixes = iter(xfixes)
	l_xfix = len(next(it_xfixes, ""))
	if l_xfix and any(map(l_xfix.__ne__, map(len, it_xfixes))):
		raise ValueError(
			"All pre- and/or suffixes must be of equal length, but got: "
				+ ", ".join(tuple(map("{!r}[{:d}]".format, xfixes, map(len, xfixes)))))
	return xfixes


def _lstrip_start(s, start, stop, prefixes):
	prefixlen = len(next(iter(prefixes), ""))
	if prefixlen:
		step = start + prefixlen
		while step <= stop:
			if all(s.find(prefix, start, step) < 0 for prefix in prefixes):
				break
			start = step
			step += prefixlen
	return start


def _rstrip_stop(s, start, stop, suffixes):
	suffixlen = len(next(iter(suffixes), ""))
	if suffixlen:
		step = stop - suffixlen
		while start <= step:
			if all(s.find(suffix, step, stop) < 0 for suffix in suffixes):
				break
			stop = step
			step -= suffixlen
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
