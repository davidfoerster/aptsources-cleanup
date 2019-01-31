# -*- coding: utf-8
"""String utilities"""

__all__ = ('startswith_token',)


def startswith_token(s, prefix, sep=None):
	"""Tests if a string is either equal to a given prefix or prefixed by it
	followed by a separator.
	"""

	if sep is None:
		return s == prefix

	prefix_len = len(prefix)
	return s.startswith(prefix) and (
		not sep or len(s) == len(prefix) or
		s.find(sep, prefix_len, prefix_len + len(sep)) == prefix_len)


def prefix(s, sep):
	pos = s.find(sep)
	return s[:pos] if pos >= 0 else s
