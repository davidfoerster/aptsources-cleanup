from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ('terminal_size', 'get_terminal_size')

import struct
import fcntl
import termios
import collections


terminal_size = collections.namedtuple('terminal_size', ('columns', 'lines'))


def get_terminal_size(fd=1):
	"""A fall-back implementation of os.get_terminal_size()"""

	lines, columns = struct.unpack(b'hh',
		fcntl.ioctl(fd, termios.TIOCGWINSZ, b'\0' * 4))
	return terminal_size(columns, lines)
