# -*- coding: utf-8
"""Filesystem-related utilities"""

__all__ = ('samefile', 'remove_sources_files')

from .gettext import _
from .terminal import termwrap
import sys
import os, os.path
import errno


def samefile(a, b):
	"""Like os.path.samefile() but return False on error."""

	try:
		return os.path.samefile(a, b)
	except EnvironmentError:
		return False


def remove_sources_files(filename):
	"""Remove the list of a sources list file and its '*.save' companion.

	Returns a tuple of a status code to indicate failure and the number of
	removed files not including '*.save' (0 or 1). Failure to remove the
	'*.save' companion is displayed but disregarded.
	"""

	rv = 0
	removed_count = 0
	for may_fail_missing, f in enumerate((filename, filename + '.save')):
		try:
			os.remove(f)
		except EnvironmentError as ex:
			if not (may_fail_missing and ex.errno == errno.ENOENT):
				rv |= 1
				termwrap.stderr().print('{:s}: {!s}'.format(_('Error'), ex))
		else:
			removed_count += not may_fail_missing
			termwrap.stderr().print(_("'{path:s}' removed.").format(path=f))

	return rv, removed_count
