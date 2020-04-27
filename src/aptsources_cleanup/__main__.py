# -*- coding: utf-8
from .util.terminal import *
from .util.operator import methodcaller, peek
from .util.itertools import *
from .util.fileutils import *
from .util.gettext import *
from .util.relations import *
from .util.strings import *
from .util.io import *
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
import aptsources_cleanup


argparse._ = _
argparse.ngettext = _N


def main(args=None):
	"""Main program entry point

	See the output of the '--help' option for usage.
	"""

	if args is None:
		args = sys.argv[1:]
	args = parse_args(args)
	if args.debug_import_fail:
		from .util.import_check import import_check
		import_check('aptsources.sourceslist', 'apt', None, args.debug_import_fail)

	sourceslist = aptsources.sourceslist.SourcesList(False)

	rv = 0
	if args.debug_sources_dir is not None:
		rv = load_sources_dir(sourceslist, args.debug_sources_dir)

	if rv == 0:
		rv = handle_duplicates(sourceslist,
			args.apply_changes, args.equivalent_schemes)

	if rv == 0 and args.apply_changes is not False:
		rv = handle_empty_files(sourceslist)

	return rv


def load_sources_dir(sourceslist, dirname):
	if not os.path.isdir(dirname):
		termwrap.stderr().print(': '.join(
			(_('Error'), _('No such directory'), dirname)))
		return 1

	import glob
	sourceslist.list.clear()
	foreach(sourceslist.load,
		glob.iglob(os.path.join(dirname, "**/*.list"), recursive=True))
	return 0


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

		super().__init__(
			prog, indent_increment, max_help_position, width)


	def _fill_text(self, text, width, indent):
		return '\n'.join(reduce(
			self._accumulate_paragraph_lines, map(
				textwrap.TextWrapper(
					width=width, initial_indent=indent, subsequent_indent=indent).wrap,
				text.split('\n\n'))))


	@staticmethod
	def _accumulate_paragraph_lines(accumulator_list, lines):
		accumulator_list.append('')
		accumulator_list += lines
		return accumulator_list


	def add_epilog(self, items):
		if items and items is not argparse.SUPPRESS:
			self._add_item(self._format_epilog, (items,))


	def _format_epilog(self, items):
		return '\n'.join(reduce(
			fpartial(peek, list.extend), starmap(self._wrap_definition, items)))


	def _wrap_definition(self, def_, desc):
		lsep = ':'
		rsep = ' '
		lines = textwrap.wrap(def_ + lsep, self._width)
		if len(lines[-1]) + len(rsep) + len(desc) <= self._width:
			lines[-1] = rsep.join((lines[-1], desc))
		else:
			indent = ' ' * self._indent_increment
			lines += textwrap.wrap(desc, self._width,
				break_on_hyphens=False, break_long_words=False,
				initial_indent=indent, subsequent_indent=indent)
		return lines


	def _format_actions_usage(self, actions, groups):
		return (
			super()._format_actions_usage(
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
		super().__init__(option_strings, dest, 0, help=help)
		self.version = version


	def __call__(self, parser, namespace, values, option_string):
		version = self.version
		if version is None:
			version = getattr(parser, 'version', None)
		if version is None:
			if __package__ and __name__ == '__main__':
				version = getattr(sys.modules[__package__], '__version__', None)
			else:
				version = globals().get('__version__')
		if version is not None:
			version = '%(prog)s, version ' + version.replace('%', '%%')

		parser._print_message(
			parser._get_formatter()._format_text(version).strip() + '\n',
			sys.stdout)
		parser.exit()


def parse_args(args):
	suppress_debug = (
		None if args and '--help-debug' in args else argparse.SUPPRESS)

	translations.add_fallback(
		DictTranslations(ID_DESCRIPTION=
			prefix(aptsources_cleanup.__doc__, '\n\n\n', reverse=True).strip()))

	ap = MyArgumentParser(formatter_class=TerminalHelpFormatter,
		add_help=False, description=_('ID_DESCRIPTION'),
		epilog=(
			(_('Author'), 'David P. W. Foerster'),
			(_('Source code and bug tracker location'),
				'https://github.com/davidfoerster/aptsources-cleanup')))

	ap.add_argument('-y', '--yes',
		dest='apply_changes', action='store_const', const=True,
		help=_('Apply all non-destructive changes without question.'))
	ap.add_argument('-n', '--no-act', '--dry-run',
		dest='apply_changes', action='store_const', const=False,
		help=_('Never apply changes; only print what would be done.'))
	noarg_equivalent_schemes = EquivalenceRelation(
		(('http', 'https', 'ftp'),), settype="ordered")
	ap.add_argument('--equivalent-schemes', metavar='SCHEMES',
		type=fpartial(EquivalenceRelation.parse, settype="ordered"),
		default=noarg_equivalent_schemes,
		help=_('Specify URI schemes that you consider equivalent using a list of '
			'equivalence classes delimited by semicolons (";") and elements '
			'delimited by commas (","). Defaults to "{:|,|;|a}". The empty argument '
			'disables this feature.')
				.format(noarg_equivalent_schemes))
	ap.add_argument('-h', '--help',
		action='help', default=argparse.SUPPRESS,
		help=_('show this help message and exit'))
	ap.add_argument('--version', action=VersionAction)

	dg = ap.add_argument_group(_('Debugging Options'),
		_('For wizards only! Use these if you know and want to test the '
			'application source code.'))
	dg.add_argument('--debug-import-fail', '--d-i-f', metavar='LEVEL',
		nargs='?', type=int, const=1, default=0,
		help=suppress_debug or
			_("Force an ImportError for the '{module:s}' module and fail on all "
					"subsequent diagnoses.")
				.format(module='aptsources.sourceslist'))
	debug_sources_dir = './test/sources.list.d'
	dg.add_argument('--debug-sources-dir', '--d-s-d', metavar='DIR',
		nargs='?', const=debug_sources_dir,
		help=suppress_debug or
			_("Load sources list files from this directory instead of the default "
					"root-owned '{default:s}'. If omitted DIR defaults to '{const:s}'.")
				.format(default='/etc/apt/sources.list*', const=debug_sources_dir))
	dg.add_argument('--debug-choices-print', '--d-c-p',
		action='store_true', default=False,
		help=suppress_debug or
			_('Debug the display of translated and formatted choices options.'))
	dg.add_argument('--help-debug',
		action='help', default=argparse.SUPPRESS,
		help=_('Show help for debugging options.'))

	args, unkown = ap.parse_known_args(args)
	if unkown:
		ap.error('\n'.join((
			_('unrecognized arguments: %s') % ' '.join(unkown),
			_("Use '{help_opt:s}' to display the program help.")
				.format(help_opt='--help'))))

	Choices.debug = args.debug_choices_print

	return args


def handle_duplicates(sourceslist, apply_changes=None,
	equivalent_schemes=None
):
	"""Interactive disablement of duplicate source entries"""

	stdout = termwrap.stdout()
	stdout_indent1 = stdout.copy(
		subsequent_indent=stdout.subsequent_indent + ' ' * 4)
	stdout_indent2 = stdout_indent1.copy(
		initial_indent=stdout_indent1.subsequent_indent)

	duplicates = tuple(get_duplicates(
		sourceslist, equivalent_schemes=equivalent_schemes))
	if duplicates:
		for dupe_set in duplicates:
			dupe_set = iter(
				sort_dupe_set_by_scheme_class(equivalent_schemes, dupe_set))
			orig = next(dupe_set)
			for dupe in dupe_set:
				stdout.print(_('Overlapping source entries:'))
				for i, se in enumerate((orig, dupe), 1):
					stdout_indent1.print(
						_("{ordinal:2d}. file {file!r}:")
							.format(ordinal=i, file=se.file))
					stdout_indent2.print(se.line)
				stdout.print(_("I disabled all but the first entry."), end="\n\n")
				dupe.disabled = True

		stdout.print(
			_N('{nduplicates:d} source entry was disabled',
				'{nduplicates:d} source entries were disabled',
				len(duplicates)).format(nduplicates=len(duplicates)) + ':')
		stdout_indent2.initial_indent = stdout_indent2.initial_indent[:-2]
		stdout_indent2.print_all(map(str, itertools.chain(*duplicates)), sep='\n')

		if apply_changes is None:
			stdout.file.write('\n')
			answer = (
				Choices(_U('yes'), _U('no'), default='no')
					.ask(_('Do you want to save these changes?')))
			apply_changes = answer is not None and answer.orig == 'yes'
			if not apply_changes:
				termwrap.stderr().print(_('Aborted.'))
				return 2

		if apply_changes:
			sourceslist.save()

	else:
		stdout.print(_('No duplicate entries were found.'))

	return 0


def sort_dupe_set_by_scheme_class(eqclasses, dupe_set):
	if eqclasses and dupe_set:
		schemes_class = eqclasses.get_class(dupe_set[0].parsed_uri.scheme)
		if schemes_class and getattr(schemes_class, "index", None) is not None:
			dupe_set.sort(key=lambda se: schemes_class.index(se.parsed_uri.scheme))
	return dupe_set


def handle_empty_files(sourceslist):
	"""Interactive removal of sources list files without valid enabled entries"""

	rv = 0
	total_count = 0
	removed_count = 0

	stdout = termwrap.stdout()
	choices = Choices(
		_U('yes'), _U('no'), _U('all'), _U('none'), _U('display'),
		default='no')
	on_eof = choices.orig['none']
	answer = None

	for total_count, source_entries in enumerate(get_empty_files(sourceslist), 1):
		file = source_entries[0].file

		while answer is None:
			stdout.file.write('\n')
			stdout.print(
				_("'{file:s}' contains no valid and enabled repository lines.")
					.format(file=file))
			answer = choices.ask(_('Do you want to remove it?'), on_eof=on_eof)
			if answer is not None and answer.orig == 'display':
				display_file(file)
				answer = None

		if answer.orig in ('yes', 'all'):
			rv2, rc2 = remove_sources_files(file)
			rv |= rv2
			if rc2:
				removed_count += rc2
				foreach(sourceslist.remove, source_entries)

		if answer.orig not in ('all', 'none'):
			answer = None

	if total_count:
		stdout.file.write('\n')
		stdout.print(
			_('{nremoved:d} of {ntotal:d} empty sourcelist files removed.')
				.format(nremoved=removed_count, ntotal=total_count))

	return rv


if __name__ == '__main__':
	try:
		locale.setlocale(locale.LC_ALL, '')
	except locale.Error as ex:
		termwrap.stderr().print(
			'Warning: Cannot set locale: ' + str(ex), end='\n\n')

	sys.stdout = replace_TextIOWrapper(sys.stdout, errors='namereplace')
	sys.stderr = replace_TextIOWrapper(sys.stderr, errors='namereplace')

	try:
		rv = main()
	except KeyboardInterrupt:
		rv = 2

	if rv:
		sys.exit(rv)
