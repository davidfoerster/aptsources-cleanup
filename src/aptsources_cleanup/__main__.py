# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals
from .util._3to2 import *
from .util.io import *
from .util.terminal import *
from .util.operator import methodcaller, peek
from .util.itertools import *
from .util.filesystem import *
from .util.gettext import *
from . import *
import sys
import os.path
import itertools
import argparse
import locale
import textwrap
from itertools import starmap
from functools import reduce, partial as fpartial
import aptsources.sourceslist
aptsources_cleanup = sys.modules[__package__]


argparse._ = _
argparse.ngettext = _N


def main(*args):
	"""Main program entry point

	See the output of the '--help' option for usage.
	"""

	args = parse_args(args or sys.argv[1:])
	if args.debug_import_fail:
		from .util.import_check import import_check
		import_check('aptsources.sourceslist', 'apt', None, args.debug_import_fail)

	sourceslist = aptsources.sourceslist.SourcesList(False)
	if args.debug_sources_dir is not None:
		if not os.path.isdir(args.debug_sources_dir):
			print(_('Error'), _('No such directory'), args.debug_sources_dir,
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


class MyArgumentParser(argparse.ArgumentParser):

	def format_help(self):
		formatter = self._get_formatter()

		# usage
		formatter.add_usage(self.usage, self._actions,
			self._mutually_exclusive_groups)

		# description
		formatter.add_text(self.description)

		# positionals, optionals and user-defined groups
		for action_group in self._action_groups:
			formatter.start_section(action_group.title)
			formatter.add_text(action_group.description)
			formatter.add_arguments(action_group._group_actions)
			formatter.end_section()

		# epilog
		formatter.add_epilog(self.epilog)

		# determine help from format above
		return formatter.format_help()


class TerminalHelpFormatter(argparse.HelpFormatter):

	def __init__(self, prog, indent_increment=2, max_help_position=18, width=-2):
		if width is not None and width <= 0:
			termwidth = termwrap.stdout().width
			width = max(termwidth + width, 32) if termwidth > 0 else None

		if width is not None:
			max_help_position = min(max_help_position, width // 3)

		super(TerminalHelpFormatter, self).__init__(
			prog, indent_increment, max_help_position, width)


	def _fill_text(self, text, width, indent):
		return '\n'.join(self._split_lines_gen(
			text, width, initial_indent=indent, subsequent_indent=indent))


	def _split_lines_gen(self, text, width, **kwargs):
		for i, paragraph in enumerate(text.split('\n\n')):
			paragraph = textwrap.wrap(paragraph, width, **kwargs)
			if not i:
				text = paragraph
			else:
				text.append('')
				text += paragraph

		return text


	def add_epilog(self, items):
		if items and items is not argparse.SUPPRESS:
			self._add_item(self._format_epilog, (items,))


	def _format_epilog(self, items):
		return '\n'.join(reduce(
			fpartial(peek, list.extend), starmap(self._wrap_definition, items)))


	def _wrap_definition(self, _def, desc):
		lsep = ':'
		rsep = ' '
		lines = textwrap.wrap(_def + lsep, self._width)
		if len(lines[-1]) + len(rsep) + len(desc) <= self._width:
			lines[-1] += rsep + desc
		else:
			indent = ' ' * self._indent_increment
			lines += textwrap.wrap(desc, self._width,
				break_on_hyphens=False, break_long_words=False,
				initial_indent=indent, subsequent_indent=indent)
		return lines


	def _format_actions_usage(self, actions, groups):
		return (
			super(TerminalHelpFormatter, self)._format_actions_usage(
				tuple(filterfalse(
					methodcaller(isinstance, (argparse._HelpAction, VersionAction)),
				actions)),
				groups))




if __debug__:
	for name in ('_fill_text', '_format_actions_usage'):
		assert callable(getattr(TerminalHelpFormatter.__base__, name, None)), (
			'Looks like there was an incompatible change in the private API of '
			'{0.__module__:s}.{0.__qualname__:s}.{1:s}().'
				.format(TerminalHelpFormatter.__base__, name))
	del name


class VersionAction(argparse.Action):

	def __init__(self, option_strings, version=None, dest=argparse.SUPPRESS,
		default=argparse.SUPPRESS, help=None
	):
		if help is None:
			help = _("Show program's version number and exit.")
		super(VersionAction, self).__init__(option_strings, dest, 0, help=help)
		self.version = version


	def __call__(self, parser, namespace, values, option_string):
		version = self.version
		if version is None:
			try:
				version = parser.version
			except AttributeError:
				pass
		if version is None:
			try:
				if __package__ and __name__ == '__main__':
					version = sys.modules[__package__].__version__
				else:
					version = __version__
			except (NameError, AttributeError):
				pass
			else:
				if version is not None:
					version = '%(prog)s, version ' + version

		parser._print_message(
			parser._get_formatter()._format_text(version).strip() + '\n',
			sys.stdout)
		parser.exit()


translations.add_fallback(DictTranslations(
	ID_DESCRIPTION=aptsources_cleanup.__doc__.rpartition('\n\n\n')[0].strip()))


def parse_args(args):
	debug = None if args and '--help-debug' in args else argparse.SUPPRESS

	ap = MyArgumentParser(formatter_class=TerminalHelpFormatter,
		add_help=False, description=_('ID_DESCRIPTION'),
		epilog=(
			(_('Author'), 'David P. W. Foerster'),
			(_('Source code and bug tracker location'),
				'https://github.com/davidfoerster/aptsources-cleanup')))

	ap.add_argument('-y', '--yes',
		dest='apply_changes', action='store_const', const=True,
		help=_('Apply all changes without question.'))
	ap.add_argument('-n', '--no-act', '--dry-run',
		dest='apply_changes', action='store_const', const=False,
		help=_('Never apply changes; only print what would be done.'))
	ap.add_argument('-h', '--help',
		action='help', default=argparse.SUPPRESS,
		help=_('show this help message and exit'))
	ap.add_argument('--version', action=VersionAction)

	dg = ap.add_argument_group(_('Debugging Options'),
		_('For wizards only! Use these if you know and want to test the '
				'application source code.'))
	dg.add_argument('--debug-import-fail', '--d-i-f', metavar='LEVEL',
		nargs='?', type=int, const=1, default=0,
		help=debug or
			_("Force an ImportError for the '{module:s}' module and fail on all "
					"subsequent diagnoses.")
				.format(module='aptsources.sourceslist'))
	debug_sources_dir = './test/sources.list.d'
	dg.add_argument('--debug-sources-dir', '--d-s-d', metavar='DIR',
		nargs='?', const=debug_sources_dir,
		help=debug or
			_("Load sources list files from this directory instead of the default "
					"root-owned '{default:s}'. If omitted DIR defaults to '{const:s}'.")
				.format(default='/etc/apt/sources.list*', const=debug_sources_dir))
	dg.add_argument('--help-debug',
		action='help', default=argparse.SUPPRESS,
		help=_('Show help for debugging options.'))

	return ap.parse_args(args)


def handle_duplicates(sourceslist, apply_changes=None):
	"""Interactive disablement of duplicate source entries"""

	duplicates = tuple(get_duplicates(sourceslist))
	if duplicates:
		for dupe_set in duplicates:
			orig = dupe_set.pop(0)
			for dupe in dupe_set:
				print(_(
'''Overlapping source entries:
  1. file {orig_file:s}:
     {orig_line:s}
  2. file {dupe_file:s}:
     {dupe_line:s}
I disabled the latter entry.''')
						.format(orig_file=orig.file, orig_line=orig.line.strip(),
							dupe_file=dupe.file, dupe_line=dupe.line.strip()),
					end='\n\n')
				dupe.disabled = True

		print(
			_N('{nduplicates:d} source entry was disabled',
				'{nduplicates:d} source entries were disabled',
				len(duplicates)).format(nduplicates=len(duplicates)) + ':',
			*itertools.chain(*duplicates), sep='\n  ')

		if apply_changes is None:
			choices = Choices(_U('yes'), _U('no'), default='no')
			print()
			answer = choices.ask(_('Do you want to save these changes?'))
			if answer is None or answer.orig != 'yes':
				print(_('Aborted.'), file=sys.stderr)
				return 2
		if apply_changes is not False:
			sourceslist.save()

	else:
		print(_('No duplicate entries were found.'))

	return 0


def handle_empty_files(sourceslist):
	"""Interactive removal of sources list files without valid enabled entries"""

	rv = 0
	total_count = 0
	removed_count = 0

	choices = Choices(
		_U('yes'), _U('no'), _U('all'), _U('none'), _U('display'),
		default='no')
	on_eof = choices.orig['none']
	answer = None

	for file, source_entries in get_empty_files(sourceslist):
		total_count += 1

		while answer is None:
			print()
			answer = choices.ask(
				_("'{file:s}' contains no valid and enabled repository lines.  Do you want to remove it?").format(file=file),
				on_eof=on_eof)
			if answer is not None and answer.orig == 'display':
				display_file(file)
				answer = None

		if answer.orig in ('yes', 'all'):
			rv2, rc2 = remove_sources_files(file)
			rv |= rv2
			removed_count += rc2
			if rc2:
				foreach(sourceslist.remove, source_entries)

		if answer.orig not in ('all', 'none'):
			answer = None

	if total_count:
		print('\n',
			_('{nremoved:d} of {ntotal:d} empty sourcelist files removed.')
				.format(nremoved=removed_count, ntotal=total_count),
			sep='')

	return rv


if __name__ == '__main__':
	locale.setlocale(locale.LC_ALL, '')
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		sys.exit(2)
