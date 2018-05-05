from __future__ import print_function, division, absolute_import, unicode_literals
from ._3to2 import *
from .itertools import filterfalse
import sys
import os
import os.path
import stat
import errno
import zipfile as _zipfile

__all__ = set(_zipfile.__all__)
__all__.discard('BadZipfile')


_filesystem_encoding = sys.getfilesystemencoding()

_MAX_PATH = 64 << 10


def strerror(errno, *args):
	return OSError(errno, os.strerror(errno), *args)


class ZipFile(_zipfile.ZipFile):

	def getinfo(self, name, resolve_symlinks=False, pwd=None, fail_missing=True):
		if resolve_symlinks:
			return self._resolve_path(name, pwd, fail_missing)
		if isinstance(name, ZipInfo):
			return name
		return self._check_missing(self.NameToInfo.get(name), name, fail_missing)


	def open(self, path, mode='r', pwd=None, resolve_symlinks=False,
		fail_missing=True
	):
		path = self.getinfo(path, resolve_symlinks, pwd, fail_missing)
		if path is None:
			return None
		return super().open(path, mode, pwd)


	def _resolve_path(self, path, pwd, fail_missing):
		if isinstance(path, ZipInfo):
			path = path.filename
		inspected = []
		uninspected = path.split(os.sep)
		uninspected.reverse()
		seen_set = set()
		c_info = None
		while uninspected:
			c_info = self._resolve_path_component(
				inspected, uninspected, pwd, seen_set)
		return self._check_missing(c_info, path, fail_missing)


	def _resolve_path_component(self, inspected, uninspected, pwd, seen_set):
		c = uninspected.pop()

		if not c or c == os.curdir:
			return None

		if c == os.pardir:
			if not inspected:
				uninspected.append(c)
				raise OSError(errno.EINVAL, 'Path points outside of this archive',
					os.sep.join(reversed(uninspected)))
			inspected.pop()
			return None

		inspected.append(c)
		c_full = os.sep.join(inspected)
		c_info = self.NameToInfo.get(c_full)
		if c_info is None or not stat.S_ISLNK(c_info.external_attr >> 16):
			if self.debug >= 2:
				print(('Not a symlink', 'Does not exist')[c_info is None],
					repr(c_full), sep=': ')
			return c_info
		if len(c_full) + c_info.file_size > _MAX_PATH:
			raise strerror(errno.ENAMETOOLONG, self.filename + ':' + c_full)

		c_seen = resolved = c_full in seen_set
		if c_info.file_size == 0:
			resolved = ''
		elif not c_seen:
			seen_set.add(c_full)
			resolved = str(super().read(c_info, pwd), _filesystem_encoding)
			null = resolved.find('\0')
			if null >= 0:
				resolved = resolved[:null]
			if resolved == c or resolved == os.curdir:
				depth_countdown = 0

		if not resolved:
			raise OSError(errno.EINVAL, 'Empty symbolic link in archive',
				self.filename + ':' + c_full)
		if c_seen:
			raise strerror(errno.ELOOP, self.filename + ':' + c_full)
		if self.debug >= 2:
			print('Found symbolic link: {!r} => {!r}'.format(c_full, resolved))

		inspected.pop()
		uninspected.extend(reversed(resolved.split(os.sep)))
		return c_info


	def _check_missing(self, info, path, fail_missing):
		if info is None and fail_missing:
			raise KeyError(
				"There is no item named '{:s}' in the archive '{:s}'"
					.format(path, self.filename))
		return info


_globals = globals()
_globals.update((k, getattr(_zipfile, k))
	for k in filterfalse(_globals.__contains__, __all__))
_globals.setdefault('BadZipFile', getattr(_zipfile, 'BadZipfile', None))
del _globals

__all__.add('BadZipFile')
#__all__ = tuple(__all__)


if __name__ == '__main__':
	import argparse
	ap = argparse.ArgumentParser()
	ap.add_argument('archive', type=argparse.FileType('rb'))
	ap.add_argument('path')
	ap.add_argument('-L', '--resolve-symlinks', type=int, default=True)
	ap.add_argument('--debug', type=int, default=0)
	ap.add_argument('-d', dest='debug', action='count')
	args = ap.parse_args()

	with args.archive, ZipFile(args.archive) as archive:
		archive.debug = args.debug
		resolved_info = archive.getinfo(args.path,
			resolve_symlinks=bool(args.resolve_symlinks))
		print('{:s}: {:s} => {!r}'.format(
			archive.filename, args.path, resolved_info.filename))
