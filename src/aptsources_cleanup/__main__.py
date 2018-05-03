from __future__ import print_function, division, absolute_import, unicode_literals
from .util._3to2 import *
from .util.io import *
from .util.terminal import *
from .util.itertools import *
from .util.filesystem import *
import sys
import os.path
import itertools
import argparse
import aptsources.sourceslist
from functools import partial as fpartial

# Import from parent package without naming it explicitly
import importlib
_parent_package = importlib.import_module(__package__)
globals().update(zip(_parent_package.__all__,
	map(fpartial(getattr, _parent_package), _parent_package.__all__)))


def main(*args):
	"""Main program entry point

	See the output of the '--help' option for usage.
	"""

	args = parse_args(args or None, None)
	if args.debug_import_fail:
		from .util.import_check import import_check
		import_check('aptsources.sourceslist', 'apt', None, args.debug_import_fail)

	sourceslist = aptsources.sourceslist.SourcesList(False)
	if args.debug_sources_dir is not None:
		if not os.path.isdir(args.debug_sources_dir):
			print('Error', 'No such directory', args.debug_sources_dir,
				sep=': ', file=sys.stderr)
			return 1
		import glob
		del sourceslist.list[:]
		foreach(sourceslist.load,
			glob.iglob(os.path.join(args.debug_sources_dir, '*.list')))

	rv = handle_duplicates(sourceslist, args.apply_changes)

	if rv == 0 and args.apply_changes is not False:
		rv = handle_empty_files(sourceslist)

	return rv


def parse_args(args, debug=False):
	ap = argparse.ArgumentParser(**dict(zip(
		('description', 'epilog'),
		map(str.strip, _parent_package.__doc__.rsplit('\n\n', 1)))))

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
	debug_sources_dir = './test/sources.list.d'
	dg.add_argument('--debug-sources-dir', metavar='DIR',
		nargs='?', const=debug_sources_dir,
		help=debug or "Load sources list files from this directory instead of the default root-owned '/etc/apt/sources.list*'. If omitted DIR defaults to '{:s}'."
				.format(debug_sources_dir))

	return ap.parse_args(args)


def handle_duplicates(sourceslist, apply_changes=None):
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


def handle_empty_files(sourceslist):
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
				display_file(file)

		if answer in 'YA':
			rv2, rc2 = remove_sources_files(file)
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


sys.exit(main())
