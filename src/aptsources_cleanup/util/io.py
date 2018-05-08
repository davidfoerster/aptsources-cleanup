# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals
from ._3to2 import *
from .gettext import _
import os
import sys

__all__ = ('FileDescriptor', 'display_file', 'sendfile_all')


class FileDescriptor(object):
	"""A context manager for operating system file descriptors"""

	def __init__(self, path, mode=os.O_RDONLY, *args):
		self._fd = os.open(path, mode, *args)


	@property
	def fd(self):
		if self._fd is None:
			raise RuntimeError(
				'This file descriptor was closed or released earlier.')
		return self._fd


	def close(self):
		"""Close the underlying file descriptor."""

		if self._fd is not None:
			os.close(self._fd)
			self._fd = None


	@property
	def closed(self):
		return self._fd is None


	def release(self):
		"""Release and return the underlying file descriptor."""

		fd = self.fd
		self._fd = None
		return fd


	def __enter__(self):
		return self.fd


	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()


def display_file(filename):
	"""Copy the content of the file at a path to standard output."""

	try:
		with FileDescriptor(filename) as fd:
			sys.stdout.flush()
			if sendfile_all(sys.stdout.fileno(), fd) == 0:
				print('<', _('empty'), '>', sep='')
	except EnvironmentError as ex:
		print(_('Error'), ex, sep=': ', file=sys.stderr)


def sendfile_all(out, in_):
	"""Copies the entire content of one file descriptor to another.

	The implementation uses os.sendfile() if available or os.read()/os.write()
	otherwise.
	"""

	sendfile = getattr(os, 'sendfile', None)
	count = 0
	if sendfile:
		# Main implementation
		while True:
			r = sendfile(out, in_, count, sys.maxsize - count)
			if not r:
				break
			count += r
	else:
		# Alternative implementation
		while True:
			r = os.read(in_, 1 << 20)
			if not r:
				break
			os.write(out, r)
			count += len(r)

	return count
