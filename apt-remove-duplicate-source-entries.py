#!/usr/bin/env python3
"""
Detects and interactively deactivates duplicate Apt source entries in
`/etc/sources.list' and `/etc/sources.list.d/*.list'.
"""

from __future__ import print_function
import sys


def _get_python_packagename(basename):
	version = sys.version_info.major
	version_part = str(version) if version >= 3 else ''
	return 'python{0}-{1}'.format(version_part, basename)

try:
	import aptsources.sourceslist
except ImportError as ex:
	print(
		'Error: {0}.\n\n'
		'Do you have the \'{1}\' package installed?\n'
		'You can do so with \'sudo apt-get install {1}\'.'
			.format(ex, _get_python_packagename('apt')),
		file=sys.stderr)
	sys.exit(127)


EMPTY_COMPONENT_LIST = (None,)

def get_duplicates(sourceslist):
	"""
	Detects and returns duplicate Apt source entries.
	"""

	sentry_map = dict()
	duplicates = list()
	for se in sourceslist.list:
		if not se.invalid and not se.disabled:
			for c in (se.comps or EMPTY_COMPONENT_LIST):
				key = (se.type, se.uri, se.dist, c)
				previous_se = sentry_map.setdefault(key, se)
				if previous_se is not se:
					duplicates.append((se, previous_se))
					break

	return duplicates


def _argparse(args):
	import argparse
	parser = argparse.ArgumentParser(description=__doc__,
		epilog='Source code at: https://github.com/davidfoerster/apt-remove-duplicate-source-entries')
	parser.add_argument('-y', '--yes',
		dest='apply_changes', action='store_const', const=True,
		help='Apply all changes without question.')
	parser.add_argument('-n', '--no-act', '--dry-run',
		dest='apply_changes', action='store_const', const=False,
		help='Never apply changes; only print what would be done.')
	return parser.parse_args(args)


def _main(args):
	input = getattr(__builtins__, 'raw_input', __builtins__.input)

	args = _argparse(args)
	sourceslist = aptsources.sourceslist.SourcesList(False)
	duplicates = get_duplicates(sourceslist)

	if duplicates:
		for dupe, orig in duplicates:
			print(
				'Overlapping source entries:\n'
				'  1. {0}: {1}\n'
				'  2. {2}: {3}\n'
				'I disabled the latter entry.'.format(
					orig.file, orig, dupe.file, dupe),
				end='\n\n')
			dupe.disabled = True

		print('\n{0} source entries were disabled:'.format(len(duplicates)),
			*[dupe for dupe, orig in duplicates], sep='\n  ', end='\n\n')

		if args.apply_changes is None:
			if input('Do you want to save these changes? (y/N) ').upper() != 'Y':
				return 2
		if args.apply_changes is not False:
			sourceslist.save()

	else:
		print('No duplicate entries were found.')

	return 0


if __name__ == '__main__':
	sys.exit(_main(sys.argv[1:]))
