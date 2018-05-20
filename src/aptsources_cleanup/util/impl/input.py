from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ('input',)

from __builtin__ import unicode as str, str as bytes, raw_input
import sys, locale


def input(prompt=None):
	"""Wraps 'raw_input' and encodes its return value

	Using the encoding of sys.stdin if available, or the preferred encoding of
	the current locale.
	"""

	answer = raw_input() if prompt is None else raw_input(prompt)
	return str(answer, sys.stdin.encoding or locale.getpreferredencoding())
