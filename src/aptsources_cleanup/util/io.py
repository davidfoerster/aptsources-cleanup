# -*- coding: utf-8
"""Various I/O-related utilities"""
__all__ = ('FileDescriptor', 'sendfile_all')

import os
import sys


class FileDescriptor:
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


def sendfile_all(out, in_):
	"""Copies the entire content of one file descriptor to another.

	The implementation uses os.sendfile() if available or os.read()/os.write()
	otherwise.
	"""

	count = 0
	while True:
		r = os.sendfile(out, in_, count, sys.maxsize - count)
		if not r:
			break
		count += r

	return count
