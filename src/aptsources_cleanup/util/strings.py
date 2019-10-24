# -*- coding: utf-8
"""String utilities"""

__all__ = ('startswith_token', 'prefix')


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


def prefix(s, *args, reverse=False):
	if reverse:
		pos = s.rfind(*args)
	else:
		pos = s.find(*args)
	return s[:pos] if pos >= 0 else s
