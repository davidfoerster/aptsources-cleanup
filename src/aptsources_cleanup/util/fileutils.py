# -*- coding: utf-8
__all__ = ('display_file',)

import os
import sys
import fcntl
import contextlib
from . import io, terminal
from .gettext import _, _N, _U


def display_file(filename):
	"""Copy the content of the file at a path to standard output."""

	try:
		with contextlib.ExitStack() as es:
			fd_in = es.enter_context(io.FileDescriptor(filename))

			sys.stdout.flush()
			fd_out = sys.stdout.fileno()
			fd_out_flags = fcntl.fcntl(fd_out, fcntl.F_GETFL)
			if fd_out_flags & os.O_APPEND:
				fcntl.fcntl(fd_out, fcntl.F_SETFL, fd_out_flags & ~os.O_APPEND)
				ex.callback(fcntl.fcntl, fd_out, fcntl.F_SETFL, fd_out_flags)

			if io.sendfile_all(fd_out, fd_in) == 0:
				print('<<<{:s}>>>'.format(_('empty')))

	except EnvironmentError as ex:
		terminal.termwrap.stderr().print('{:s}: {!s}'.format(_('Error'), ex))
