# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals
from ._3to2 import *
import re
import sys
import errno
import weakref
import textwrap
import operator

__all__ = ('try_input', 'termwrap', 'TERMMODES')


TERMMODES = ('bold', 'underline smul', 'normal sgr0')

TERMMODES = map(operator.methodcaller('partition', ' '), TERMMODES)

termmodes_noctrl_pattern = '[\x00-\x1f]'

if sys.stdout and sys.stdout.isatty():
	try:
		import curses
		curses.setupterm()
	except (ImportError, OSError) as ex:
		if __debug__:
			print('Warning', ex, sep=': ', end='\n\n', file=sys.stderr)
		curses = None
else:
	curses = None

if curses is None:
	TERMMODES = dict.fromkeys(map(operator.itemgetter(0), TERMMODES), '')

	termmodes_pattern = re.compile(r'\A(?!x)x')  # Never matches

	termmodes_noctrl_pattern = re.compile(termmodes_noctrl_pattern)

else:
	TERMMODES = {
		k: (curses.tigetstr(capname or k) or b'').decode('ascii')
		for k, _, capname in TERMMODES
	}

	termmodes_pattern = re.compile(
		'|'.join(map(re.escape, filter(None, TERMMODES.values()))))

	termmodes_noctrl_pattern = re.compile(
		termmodes_pattern.pattern + '|' + termmodes_noctrl_pattern)


try:
	from os import terminal_size, get_terminal_size

except ImportError:
	import struct, fcntl, termios, collections

	terminal_size = collections.namedtuple(
		'terminal_size', ('columns', 'lines'))

	def get_terminal_size(cls, fd=1):
		"""A fall-back implementation of os.get_terminal_size()"""

		lines, columns = struct.unpack(b'hh',
			fcntl.ioctl(fd, termios.TIOCGWINSZ, b'\x00\x00\x00\x00'))
		return terminal_size(columns, lines)


def try_input(prompt=None, on_eof='', end='\n? '):
	"""Similar to input() but return a default response on EOF or EBADF.

	If input() fails with EOFError or due to a bad (e. g. closed) standard output
	stream return 'on_eof' instead which defaults to the empty string.

	Additionally wrap the prompt string using termwrap (see below). 'end' is
	always appended to the prompt and defaults to '\n? '.
	"""

	if prompt:
		termwrap.stdout().print(prompt, end=end)
		end = ''

	try:
		return input(end)
	except (EOFError, KeyboardInterrupt):
		pass
	except EnvironmentError as ex:
		if ex.errno != errno.EBADF:
			raise
	return on_eof


class termwrap(textwrap.TextWrapper):
	"""Text wrapping for terminal output"""

	try:
		__base__
	except NameError:
		__base__ = textwrap.TextWrapper

	_instances = {}


	@classmethod
	def get(cls, file=None, use_weakref=True, ignore_errors=True):
		"""Retrieves a termwrap instance for the given file object.

		Missing instances are created on demand using weak references unless
		'use_weakref' is False. Errors during terminal size detection are
		suppressed unless 'ignore_errors' is False.

		'file' defaults to None which is equivalent to the current value of
		sys.stdout.
		"""

		if file is None:
			file = sys.stdout

		tw = cls._instances.get(id(file))
		if isinstance(tw, weakref.ref):
			tw = tw()

		if tw is None:
			try:
				tw = cls(file)
			except EnvironmentError:
				if not ignore_errors:
					raise
				tw = cls()
				tw.file = file
			cls._instances[id(file)] = weakref.ref(tw) if use_weakref else tw

		return tw


	@classmethod
	def stdout(cls):
		"""Convenience method for get(sys.stdout)"""
		return cls.get()

	@classmethod
	def stderr(cls):
		"""Convenience method for get(sys.stderr)"""
		return cls.get(sys.stderr)


	def __init__(self, file=None, width=0, **kwargs):
		"""Initialize with the given parameters as with textwrap.TextWrapper.

		If 'file' is not None and 'with' < 0 the width is initialized to the
		current terminal width if available.
		"""

		if file is not None and width <= 0:
			width = self._refresh_width_impl(file)
		self.__base__.__init__(self, width=width, **kwargs)
		self.file = file


	def print(self, paragraph, end='\n', return_last_line_len=False):
		"""Prints a paragraph to the stored file object."""
		if self.file is None:
			raise TypeError
		if self.width > 0:
			paragraph = self.wrap(paragraph)
		else:
			assert isinstance(paragraph, str)
			paragraph = (paragraph,)

		print(*paragraph, sep='\n', end=end, file=self.file)

		if return_last_line_len:
			return self._get_last_line_len(paragraph[-1], end)


	def print_all(self, paragraphs, end='\n', sep='\n\n',
		return_last_line_len=False
	):
		"""Prints a sequence of paragraph to the stored file object."""
		if self.file is None:
			raise TypeError
		if self.width > 0:
			paragraphs = map(self.fill, paragraphs)
		if return_last_line_len:
			paragraphs = tuple(paragraphs)

		print(*paragraphs, sep=sep, end=end, file=self.file)

		if return_last_line_len:
			return self._get_last_line_len(paragraphs[-1], end)


	@staticmethod
	def _get_last_line_len(s, end):
		n = len(end)
		p = end.rfind('\n') + 1
		if p:
			return n - p

		n += len(s)
		p = s.rfind('\n') + 1
		if p:
			return n - p

		return n


	def refresh_width(self, file=None):
		"""Sets the wrapping width to the current width of the associated terminal.

		If the associated file descriptor does not report a terminal width the
		current width value is retained.
		"""
		width = self._refresh_width_impl(self.file if file is None else file)
		if width > 0:
			self.width = width
		return width > 0


	@staticmethod
	def _refresh_width_impl(file):
		if not file.isatty():
			return 0
		return get_terminal_size(file.fileno()).columns
