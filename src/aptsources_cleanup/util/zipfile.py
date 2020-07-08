# -*- coding: utf-8
import sys
import os
import io
import stat
import errno
import operator
import functools
from . import os, strings, collections
from .itertools import filterfalse
from .operator import methodcaller, identity as _sanitize_path_sep

from zipfile import *
import zipfile as _zipfile
__all__ = _zipfile.__all__


if os.sep != "/":
	_sanitize_path_sep = methodcaller(str.replace, os.sep, "/")


class ZipFile(_zipfile.ZipFile):
	"""Extends zipfile.ZipFile with in-archive resolution of symbolic links"""

	_max_path = 64 << 10


	def getinfo(self, name, pwd=None, *, follow_symlinks=False,
		fail_missing=True
	):
		if follow_symlinks:
			return self._resolve_path(name, pwd, fail_missing)
		if isinstance(name, ZipInfo):
			return name
		name = os.fspath(name)
		return self._check_missing(self.NameToInfo.get(name), name, fail_missing)


	def open(self, path, mode='r', pwd=None, *, follow_symlinks=False,
		fail_missing=True, **kwargs
	):
		path = self.getinfo(
			path, pwd, follow_symlinks=follow_symlinks, fail_missing=fail_missing)
		return path and super().open(path, mode, pwd, **kwargs)


	def read(self, path, pwd=None, *, follow_symlinks=True, fail_missing=True):
		path = self.getinfo(
			path, pwd, follow_symlinks=follow_symlinks, fail_missing=fail_missing)
		return path and super().read(path, pwd)


	def extract(self, member, path=None, pwd=None, *, follow_symlinks=False,
		fail_missing=True
	):
		member = self.getinfo(
			member, pwd, follow_symlinks=follow_symlinks, fail_missing=fail_missing)
		success = member is not None
		if success:
			super().extract(member, path, pwd)
		return success


	def _resolve_path(self, path, pwd, fail_missing):
		if isinstance(path, ZipInfo):
			path = path.filename
		else:
			path = _sanitize_path_sep(os.fspath(path))
		assert os.sep == "/" or os.sep not in path
		is_dir = path.endswith("/")
		path = path.strip("/")

		inspected = []
		uninspected = path.split("/")
		uninspected.reverse()
		seen_set = collections.ExtSet()
		c_info = None

		while uninspected:
			c_info = self._resolve_path_component(
				inspected, uninspected, pwd, seen_set)

		if is_dir and inspected:
			inspected.append("")
			c_info = self.NameToInfo.get("/".join(inspected))

		return self._check_missing(c_info, path, fail_missing)


	def _resolve_path_component(self, inspected, uninspected, pwd, seen_set):
		c = uninspected.pop()
		#_eprintf('_resolve_path_component(): {!r}, {!r}, {!r}', inspected, c, uninspected)

		if not c or c == os.curdir:
			return None

		if c == os.pardir:
			if not inspected:
				uninspected.append(c)
				uninspected.reverse()
				raise self._OSError(
					errno.ENOENT, 'Path points outside of this archive',
					"/".join(uninspected))
			inspected.pop()
			return None

		inspected.append(c)
		c_full = "/".join(inspected)
		c_info = self.NameToInfo.get(c_full)
		if c_info is None or not stat.S_ISLNK(c_info.external_attr >> 16):
			if self.debug >= 2:
				_eprintf('{:s}: {!r}',
					('Not a symlink', 'Does not exist')[c_info is None],
					':'.join((self.filename, c_full)))
			return c_info
		if c_info.is_dir():
			raise BadZipFile(
				"{:s}:{!r} claims to be both a directory and a symbolic link."
					.format(self.filename, c_info))
		if len(c_info.filename) - len(c) + c_info.file_size > self._max_path:
			raise self._OSError(errno.ENAMETOOLONG, None, c_info.filename)

		if not seen_set.add(c_info.filename):
			raise self._OSError(errno.ELOOP, None, c_info.filename)
		uninspected.extend(reversed(
			self._read_symlink(c_info, pwd).rstrip("/").split("/")))
		inspected.pop()
		return c_info


	def _read_symlink(self, info, pwd):
		if info.flag_bits & 0x800:
			encoding = "utf-8"
			errmsg = None
		else:
			encoding = "ascii"
			errmsg = (
				"Non-ASCII character in symbolic link with legacy file name encoding")

		with io.TextIOWrapper(super().open(info, "r", pwd), encoding) as fp:
			try:
				target = fp.read(self._max_path)
			except UnicodeDecodeError:
				raise self._OSError(errno.EILSEQ, errmsg, info.filename)
			assert not fp.read(1), (
				"The size of {info.filename!r} inside {self.filename!r} "
				"({info.file_size:d}) exceeds "
				"{type.__module__:s}.{type.__qualname__:s}._max_path "
				"({self._max_path:d})."
					.format(type=type(self), self=self, info=info))

		for f_test, errmsg in self._read_symlink_tests:
			if f_test is not None and f_test(target):
				raise self._OSError(errno.ENOENT, errmsg, info.filename)

		if self.debug >= 2:
			_eprintf("Found symbolic link: {!r} => {!r}",
				":".join((self.filename, info.filename)), target)

		return target


	_read_symlink_tests = (
		(operator.not_, "Empty symbolic link"),
		(methodcaller(str.startswith, "/"),
			"Absolute symbolic link target inside an archive"),
		(methodcaller(str.__contains__, "\0"), "NUL char in symbolic link"),
	)


	def _check_missing(self, info, path, fail_missing):
		if info is None and fail_missing:
			raise KeyError(
				'There is no item named {!r} in the archive {!r}'
					.format(path, self.filename))
		return info


	def _OSError(self, err, msg=None, filename=None, filename2=None):
		if filename is None:
			filename = self.filename
		else:
			filename = ':'.join((self.filename, filename))

		return OSError(err, msg or os.strerror(err), filename, None, filename2)


def _eprintf(fmt, *args):
	return print(fmt.format(*args), file=sys.stderr)


def _parse_args(args):
	import argparse

	class ArgumentParser(argparse.ArgumentParser):
		def error(self, message):
			self.exit(2,
				'{:s}Error: {:s}\nPlease use the options "-h" or "--help" for more '
					'detailled usage info.\n'
					.format(self.format_usage(), message))

	ap = ArgumentParser(
		description='Show symbolic link targets inside ZIP archives.',
		formatter_class=argparse.ArgumentDefaultsHelpFormatter, add_help=False)
	ap.add_argument('archive',
		type=argparse.FileType('rb'),
		help='Path to a ZIP archive')
	ap.add_argument('paths', nargs='+',
		help='Archive member paths to inspect')
	ap.add_argument('-L', '--follow-symlinks', metavar='N',
		type=int, default=1,
		help='Follow symbolic links during archive member inspection if N != 0.')
	ap.add_argument('-h', '--help', dest=argparse.SUPPRESS,
		action='help', help=argparse.SUPPRESS)

	apdg = ap.add_mutually_exclusive_group()
	apdg.add_argument('-d', dest='debug',
		action='count', default=0,
		help='Increase debugging level by 1. Can be specified multiple times.')
	apdg.add_argument('--debug', dest='debug',
		metavar='N', type=int, default=0,
		help='Set debugging level directly.')

	return ap.parse_args(args)


def _main(args=None):
	args = _parse_args(args)

	with args.archive, ZipFile(args.archive) as archive:
		archive.debug = args.debug
		getinfo = functools.partial(ZipFile.getinfo, archive,
			follow_symlinks=args.follow_symlinks, fail_missing=False)

		for path in args.paths:
			resolved_info = getinfo(path)
			if resolved_info is not None:
				print('{:s}: {!r} => {!r}'.format(
					archive.filename, path, resolved_info.filename))
			else:
				_eprintf(
					'{:s}: {!r} => No such archive entry or dangling symbolic link',
					archive.filename, path)


if __name__ == '__main__':
	_main()
