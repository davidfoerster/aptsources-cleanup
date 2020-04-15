# -*- coding: utf-8
__all__ = ('display_file',)

import os
import sys
import mmap
from . import io, terminal
from .gettext import _, _N, _U


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
