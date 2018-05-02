#!/usr/bin/python3 -OEs
"""Detects and interactively deactivates duplicate Apt source entries and
files without valid enabled source entries in `/etc/sources.list' and
`/etc/sources.list.d/*.list'.

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
import textwrap
import weakref

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
	import urllib.parse
except ImportError:
	class urllib:
		import urlparse as parse

try:
	import aptsources.sourceslist
except ImportError:
	if __name__ != '__main__':
		raise
	# Ignore the issue for now to perform some diagnosis later
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
	"""Detects source files without valid enabled entries.

	Returns pairs of file names and lists of their respective source entries.
	"""

	sentry_map = collections.defaultdict(list)
	for se in sourceslist.list:
		sentry_map[se.file].append(se)

	return filter(
		lambda item: all(se.disabled | se.invalid for se in item[1]),
		sentry_map.items())


def try_input(prompt=None, on_eof='', end='\n? '):
	"""Similar to input() but return a default response on EOF or EBADF.

	If input() fails with EOFError or due to a bad (e. g. closed) standard output
	stream return 'on_eof' instead which defaults to the empty string.

	Additionally wrap the prompt string using termwrap (see below). 'end' is
	always appended to the prompt and defaults to '\n? '.
	"""

	if prompt:
		termwrap.stdout().print(prompt, end=end)
		end = None

	try:
		return input(end)
	except EOFError:
		pass
	except EnvironmentError as ex:
		if ex.errno != errno.EBADF:
			raise
	return on_eof


def foreach(func, iterables):
	"""Call 'func' on each item in 'iterable'."""

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
	"""Interactive disablement of duplicate source entries"""

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
			print()
			answer = try_input(
				'Do you want to save these changes?  ([y]es/[N]o)')
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
	"""A context manager for operating system file descriptors"""

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
	"""Copy the content of the file at a path to standard output."""

	try:
		with FileDescriptor(filename) as fd:
			sys.stdout.flush()
			if sendfile_all(sys.stdout.fileno(), fd) == 0:
				print('<empty>')
	except OSError as ex:
		print('Error:', ex, file=sys.stderr)


def _remove_sources_files(filename):
	"""Remove the list of a sources list file and its '*.save' companion.

	Returns a tuple of a status code to indicate failure and the number of
	removed files not including '*.save' (0 or 1). Failure to remove the
	'*.save' companion is displayed but disregarded.
	"""

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
	"""Interactive removal of sources list files without valid enabled entries"""

	rv = 0
	total_count = 0
	removed_count = 0
	answer = None

	for file, source_entries in get_empty_files(sourceslist):
		total_count += 1

		while not answer or answer not in 'YNAO':
			print()
			answer = try_input(
				"'{:s}' contains no valid and enabled repository lines.  Do you want to remove it?  ([y]es/[N]o/[a]ll/n[o]ne/[d]isplay)".format(file),
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
	"""Main program entry point

	See the output of the '--help' option for usage.
	"""

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
	"""Like os.path.samefile() but return False on error."""

	try:
		return os.path.samefile(a, b)
	except OSError:
		return False


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


class termwrap(textwrap.TextWrapper):
	"""Text wrapping for terminal output"""

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
		textwrap.TextWrapper.__init__(self, width=width, **kwargs)
		self.file = file


	def print(self, paragraph, end='\n'):
		"""Prints a paragraph to the stored file object."""
		if self.file is None:
			raise TypeError
		if self.width > 0:
			paragraph = self.wrap(paragraph)
		else:
			paragraph = (paragraph,)
		print(*paragraph, sep='\n', end=end, file=self.file)


	def print_all(self, paragraphs, end='\n', sep='\n\n'):
		"""Prints a sequence of paragraph to the stored file object."""
		if self.file is None:
			raise TypeError
		if self.width > 0:
			paragraphs = map(self.fill, paragraphs)
		print(*paragraphs, sep=sep, end=end, file=self.file)


	def refresh_width(self, file=None):
		"""Sets the wrapping width to the current width of the associated terminal.

		If the associated file descriptor does not report a terminal width the
		current width value is retained.
		"""
		width = self._refresh_width_impl(self.file if file is None else file)
		if width > 0:
			self.width = width
		return width > 0


	@classmethod
	def _refresh_width_impl(cls, file):
		if not os.isatty(file.fileno()):
			return 0
		return cls.get_terminal_size(file.fileno()).columns


	try:
		from os import terminal_size, get_terminal_size
	except ImportError:
		import struct as _struct, fcntl as _fcntl, termios as _termios

		terminal_size = collections.namedtuple(
			'terminal_size', ('columns', 'lines'))

		@classmethod
		def get_terminal_size(cls, fd=1):
			"""A fall-back implementation of os.get_terminal_size()"""

			lines, columns = cls._struct.unpack(b'hh',
				cls._fcntl.ioctl(fd, cls._termios.TIOCGWINSZ, b'\0\0\0\0'))
			return cls.terminal_size(columns, lines)


def _check_pkg_integrity(pkg, paragraphs, debug_fail=0):
	"""Check the integrity of an installed Apt package

	...based on its checksum file and warn about possible issues.
	"""

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
			"Warning: Package integrity check failed  ('{:s} < {:s}' has exit status {:d})."
				.format(' '.join(md5sum_cmd), md5sums_file, md5sum_proc.returncode))

	return not (md5sum_proc.returncode or debug_fail)


def _import_aptsources_sourceslist(debug_fail=0):
	"""Check for possible issues during the import of the 'aptsource.sourceslist' module

	...and print warnings as appropriate.
	"""

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
			termwrap.get(sys.stderr, ignore_errors=False)
		except EnvironmentError as ex:
			print(
				'WARNING: Cannot wrap text output due a failure to get the terminal size',
				ex, sep=': ', end='\n\n', file=sys.stderr)

		termwrap.stderr().print_all(paragraphs)
		sys.exit(127)


if __name__ == '__main__':
	sys.exit(main())
