#!/usr/bin/python3 -OEs
"""Detects and interactively deactivates duplicate Apt source entries in
`/etc/sources.list' and `/etc/sources.list.d/*.list'.

Source code at https://github.com/davidfoerster/apt-remove-duplicate-source-entries
"""

from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import os
import os.path
import errno
import operator
import itertools
import collections

__all__ = ('get_duplicates', 'main')

try:
	from future_builtins import *
except ImportError:
	pass

try:
	from __builtin__ import unicode as str, str as bytes, raw_input as input, xrange as range
except ImportError:
	pass

try:
	from itertools import filterfalse
except ImportError:
	from itertools import ifilterfalse as filterfalse

try:
	import urllib.parse
except ImportError:
	class urllib:
		import urlparse as parse

try:
	import aptsources.sourceslist
except ImportError:
	if __name__ != '__main__':
		raise
	aptsources = None


def get_duplicates(sourceslist):
	"""Detects and returns duplicate Apt source entries."""

	normpath = os.path.normpath
	urlparse = urllib.parse.urlparse
	urlunparse = urllib.parse.urlunparse

	sentry_map = collections.defaultdict(list)
	for se in sourceslist.list:
		if not se.invalid and not se.disabled:
			uri = urlparse(se.uri)
			uri = urlunparse(uri._replace(path=normpath(uri.path)))
			dist = normpath(se.dist)
			for c in (se.comps or (None,)):
				sentry_map[(se.type, uri, dist, c and normpath(c))].append(se)

	return filter(lambda dupe_set: len(dupe_set) > 1, sentry_map.values())


def get_empty_files(sourceslist):
	sentry_map = collections.defaultdict(list)
	for se in sourceslist.list:
		sentry_map[se.file].append(se)

	return filter(
		lambda item: all(se.disabled | se.invalid for se in item[1]),
		sentry_map.items())


def try_input(prompt=None, on_eof=''):
	try:
		return input(prompt)
	except EOFError:
		pass
	except EnvironmentError as ex:
		if ex.errno != errno.EBADF:
			raise
	return on_eof


def foreach(func, iterables):
	for x in iterables:
		func(x)


def _argparse(args, debug=False):
	import argparse
	ap = argparse.ArgumentParser(**dict(zip(
		('description', 'epilog'), map(str.strip, __doc__.rsplit('\n\n', 1)))))

	if debug is None:
		if args is None: args = sys.argv[1:]
		debug = '--help-debug' in args
	debug = None if debug else argparse.SUPPRESS

	ap.add_argument('-y', '--yes',
		dest='apply_changes', action='store_const', const=True,
		help='Apply all changes without question.')
	ap.add_argument('-n', '--no-act', '--dry-run',
		dest='apply_changes', action='store_const', const=False,
		help='Never apply changes; only print what would be done.')

	dg = ap.add_argument_group('Debugging Options',
		'For wizards only! Use these if you know and want to test the application source code.')
	dg.add_argument('--help-debug', action='help',
		help='Show help for debugging options')
	dg.add_argument('--debug-import-fail', metavar='LEVEL',
		nargs='?', type=int, const=1, default=0,
		help=debug or "Force an ImportError for the 'aptsources.sourceslist' module and fail on all subsequent diagnoses.")
	debug_sources_dir = os.path.join(
		os.path.dirname(__file__), 'test/sources.list.d')
	dg.add_argument('--debug-sources-dir', metavar='DIR',
		nargs='?', const=debug_sources_dir,
		help=debug or "Load sources list files from this directory instead of the default root-owned '/etc/apt/sources.list*'. If omitted DIR defaults to '{:s}'."
				.format(debug_sources_dir))

	return ap.parse_args(args)


def _main_duplicates(sourceslist, apply_changes=None):
	duplicates = tuple(get_duplicates(sourceslist))
	if duplicates:
		for dupe_set in duplicates:
			orig = dupe_set.pop(0)
			for dupe in dupe_set:
				print(
'''Overlapping source entries:
  1. file {:s}:
     {:s}
  2. file {:s}:
     {:s}
I disabled the latter entry.'''
						.format(orig.file, orig.line.strip(),
							dupe.file, dupe.line.strip()),
					end='\n\n')
				dupe.disabled = True

		print('{:d} source entries were disabled:'.format(len(duplicates)),
			*itertools.chain(*duplicates), sep='\n  ')

		if apply_changes is None:
			answer = try_input('\nDo you want to save these changes? ([y]es/[N]o) ')
			if answer:
				answer = answer[0].upper()
			if answer != 'Y':
				return 2
		if apply_changes is not False:
			sourceslist.save()

	else:
		print('No duplicate entries were found.')

	return 0


class FileDescriptor:
	def __init__(self, path, mode=os.O_RDONLY, *args):
		self._fd = os.open(path, mode, *args)

	@property
	def fd(self):
		return self._fd

	def close(self):
		if self._fd is not None:
			os.close(self._fd)
			self._fd = None

	def release(self):
		fd = self._fd
		self._fd = None
		return fd

	def __enter__(self):
		return self.fd

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()


def _display_file(filename):
	try:
		with FileDescriptor(filename) as fd:
			sys.stdout.flush()
			if sendfile_all(sys.stdout.fileno(), fd) == 0:
				print('<empty>')
	except OSError as ex:
		print('Error:', ex, file=sys.stderr)


def _remove_sources_files(filename):
	rv = 0
	removed_count = 0
	for may_fail_missing, f in enumerate((filename, filename + '.save')):
		try:
			os.remove(f)
		except OSError as ex:
			if not (may_fail_missing and ex.errno == errno.ENOENT):
				rv |= 1
				print('Error:', ex, file=sys.stderr)
		else:
			removed_count += not may_fail_missing
			print("'{:s}' removed.".format(f))

	return rv, removed_count


def _main_empty_files(sourceslist):
	rv = 0
	total_count = 0
	removed_count = 0
	answer = None

	for file, source_entries in get_empty_files(sourceslist):
		total_count += 1

		while not answer or answer not in 'YNAO':
			answer = try_input(
				"\n'{:s}' contains no valid and enabled repository lines. Do you want to remove it? ([y]es/[N]o/[a]ll/n[o]ne/[d]isplay) ".format(file),
				'O')
			answer = answer[0].upper() if answer else 'N'

			if answer == 'D':
				_display_file(file)

		if answer in 'YA':
			rv2, rc2 = _remove_sources_files(file)
			rv |= rv2
			removed_count += rc2
			if rc2:
				foreach(sourceslist.remove, source_entries)

		if answer not in 'AO':
			answer = None

	if total_count:
		print(
			'\n{:d} of {:d} empty sourcelist files removed.'
				.format(removed_count, total_count))

	return rv


def main(*args):
	args = _argparse(args or None, None)
	if aptsources is None or args.debug_import_fail:
		_import_aptsources_sourceslist(args.debug_import_fail)

	sourceslist = aptsources.sourceslist.SourcesList(False)
	if args.debug_sources_dir is not None:
		import glob
		del sourceslist.list[:]
		foreach(sourceslist.load,
			glob.iglob(os.path.join(args.debug_sources_dir, '*.list')))

	rv = _main_duplicates(sourceslist, args.apply_changes)

	if rv == 0 and args.apply_changes is not False:
		rv = _main_empty_files(sourceslist)

	return rv


def samefile(a, b):
	try:
		return os.path.samefile(a, b)
	except OSError:
		return False


def sendfile_all(out, in_):
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


try:
	from os import get_terminal_size
except ImportError:
	import struct, fcntl, termios

	terminal_size = collections.namedtuple('terminal_size', ('columns', 'lines'))

	def get_terminal_size(fd=1):
		lines, columns = struct.unpack(b'hh',
			fcntl.ioctl(fd, termios.TIOCGWINSZ, b'\0\0\0\0'))
		return terminal_size(columns, lines)


def _check_pkg_integrity(pkg, paragraphs, debug_fail=0):
	import subprocess
	md5sum_cmd = ('md5sum', '--check', '--strict', '--warn', '--quiet')
	md5sums_file = '/var/lib/dpkg/info/{:s}.md5sums'.format(pkg)

	try:
		md5sums_fd = os.open(md5sums_file, os.O_RDONLY)
		try:
			md5sum_proc = subprocess.Popen(
					md5sum_cmd, cwd='/', stdin=md5sums_fd, close_fds=True)
		finally:
			os.close(md5sums_fd)
	except OSError as ex:
		paragraphs.append(
			'Warning: Cannot check package integrity ({:s}: {!s}).'
				.format(ex.__class__.__name__, ex))
		return False

	if md5sum_proc.wait() or debug_fail:
		paragraphs.append(
			"Warning: Package integrity check failed ('{:s} < {:s}' has exit status {:d})."
				.format(' '.join(md5sum_cmd), md5sums_file, md5sum_proc.returncode))

	return not (md5sum_proc.returncode or debug_fail)


def _wrap_terminal_width(paragraphs):
	if os.isatty(sys.stderr.fileno()):
		assert all('\n' not in p for p in paragraphs)
		from textwrap import TextWrapper
		text_wrapper = TextWrapper(
			width=get_terminal_size(sys.stderr.fileno()).columns)
		paragraphs = map(text_wrapper.fill, paragraphs)

	return paragraphs


def _import_aptsources_sourceslist(debug_fail=0):
	global aptsources
	try:
		import aptsources.sourceslist
		if debug_fail:
			import __nonexistant_module__ as aptsources
			raise AssertionError

	except ImportError as exception:
		python_name = 'python'
		if sys.version_info.major >= 3:
			python_name += str(sys.version_info.major)
		python_exe = '/usr/bin/' + python_name
		python_pkg = python_name + '-minimal'

		paragraphs = [
			"{0:s}: {1!s}.  Do you have the '{2:s}' package installed?  You can do so with 'sudo apt install {2:s}'."
				.format(exception.__class__.__name__, exception, python_name + '-apt')
		]

		if not samefile(python_exe, sys.executable) or debug_fail:
			paragraphs.append(
				"Warning: The current Python interpreter is '{:s}'.  Please use the default '{:s}' if you encounter issues with the import of the 'aptsources' module."
					.format(sys.executable, python_exe))

		if not _check_pkg_integrity(python_pkg, paragraphs, debug_fail):
			paragraphs[-1] += (
				"  Please make sure that the '{:s}' package wasn't corrupted and that '{:s}' refers to the Python interpreter from the same package."
					.format(python_pkg, python_exe))

		try:
			paragraphs = _wrap_terminal_width(paragraphs)
		except EnvironmentError as ex:
			print(
				'WARNING: Cannot wrap text output due a failure to get the terminal size',
				ex, sep=': ', end='\n\n', file=sys.stderr)

		print(*paragraphs, sep='\n\n', file=sys.stderr)
		sys.exit(127)


if __name__ == '__main__':
	sys.exit(main())
