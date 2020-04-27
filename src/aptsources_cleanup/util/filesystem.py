# -*- coding: utf-8
"""Filesystem-related utilities"""

__all__ = ("dirseps", "samefile")

import os


dirseps = { os.sep, os.altsep or os.sep }


def samefile(a, b):
	"""Like os.path.samefile() but return False on error."""

	try:
		return os.path.samefile(a, b)
	except EnvironmentError:
		return False
