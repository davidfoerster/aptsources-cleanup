# -*- coding: utf-8
__all__ = ('display_file',)

import sys
from . import io, terminal
from .gettext import _, _N, _U


def display_file(filename):
	"""Copy the content of the file at a path to standard output."""

	try:
		with io.FileDescriptor(filename) as fd:
			sys.stdout.flush()
			if io.sendfile_all(sys.stdout.fileno(), fd) == 0:
				print('<<<{:s}>>>'.format(_('empty')))
	except EnvironmentError as ex:
		terminal.termwrap.stderr().print('{:s}: {!s}'.format(_('Error'), ex))
