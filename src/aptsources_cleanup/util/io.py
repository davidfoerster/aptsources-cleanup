# -*- coding: utf-8
"""Various I/O-related utilities"""
__all__ = ('FileDescriptor', 'isatty')

import os


class FileDescriptor:
	"""A context manager for operating system file descriptors"""

	__slots__ = ('_fd',)


	def __init__(self, path, flags=os.O_RDONLY, mode=0o777):
		self._fd = os.open(path, flags, mode)


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


def isatty(file):
	"""Convenience method to check if a file object exists, is open, and refers
	to a TTY.
	"""

	return file is not None and not file.closed and file.isatty()
