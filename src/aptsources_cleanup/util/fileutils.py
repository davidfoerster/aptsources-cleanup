# -*- coding: utf-8
__all__ = ("display_file", "remove_sources_files")

import sys
import mmap
import errno
from . import io, os
from .gettext import _
from .terminal import termwrap


def display_file(filename):
	"""Copy the content of the file at a path to standard output."""

	try:
		with io.FileDescriptor(filename) as fd_in:
			with mmap.mmap(fd_in, 0, access=mmap.ACCESS_READ) as buf_in:
				if buf_in:
					sys.stdout.flush()
					sys.stdout.buffer.write(buf_in)
					if buf_in[-1] != ord(b'\n'):
						sys.stdout.buffer.write(b'\n')
				else:
					print('<<<{:s}>>>'.format(_('empty')))

	except EnvironmentError as ex:
		terminal.termwrap.stderr().print('{:s}: {!s}'.format(_('Error'), ex))


def remove_sources_files(filename):
	"""Remove the list of a sources list file and its '*.save' companion.

	Returns a tuple of a status code to indicate failure and the number of
	removed files not including '*.save' (0 or 1). Failure to remove the
	'*.save' companion is displayed but disregarded.
	"""

	rv = 0
	removed_count = 0
	for may_fail_missing, f in enumerate(
		(filename, os.fspath(filename) + ".save")
	):
		try:
			os.remove(f)
		except EnvironmentError as ex:
			if not (may_fail_missing and ex.errno == errno.ENOENT):
				rv |= 1
				termwrap.stderr().print("{:s}: {!s}".format(_("Error"), ex))
		else:
			removed_count += not may_fail_missing
			termwrap.stderr().print(_("'{path:s}' removed.").format(
				path=os.fspath(f)))

	return rv, removed_count
