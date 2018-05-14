# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = (
	'translation', 'translations', '_', '_N', '_U',
	'NullTranslations', 'GNUTranslations', 'DictTranslations',
	'ChoiceInfo', 'Choices'
)

from ._3to2 import *
from . import terminal
from . import functools
from . import collections
from .strings import startswith_token
from .operator import identity, methodcaller, peek
from .itertools import unique, last
from .functools import LazyInstance, comp, partial as fpartial
from .zipfile import ZipFile
import gettext as _gettext
import re
import string
import operator
import sys
import os
import os.path
import errno
import locale
import unicodedata
from itertools import islice, starmap
from gettext import NullTranslations, GNUTranslations


def _get_archive():
	try:
		return __loader__.archive
	except (NameError, AttributeError):
		return None


def get_localedir(locales_subdir='share/locales'):
	src_root = os.path.dirname(os.path.dirname(
		sys.modules[(__package__ or __name__).partition('.')[0]].__file__))
	src_root_locales = os.path.join(src_root, locales_subdir)

	if _get_archive() is None and not os.path.isdir(src_root_locales):
		src_root_parent_locales = os.path.join(
			os.path.dirname(src_root), locales_subdir)
		if os.path.isdir(src_root_parent_locales):
			return src_root_parent_locales

	return src_root_locales


def get_languages():
	langs = os.environ.get('LANGUAGE', '').split(':')

	loc = locale.getlocale(locale.LC_MESSAGES)[0]
	if loc:
		loc = loc.partition('.')[0]
		if loc:
			langs.append(loc)

	if not any(langs):
		langs = ('C',)

	return langs


def translation(domain, localedir=None, languages=None, _class=None,
	fallback=False, codeset=None
):
	"""Similar to gettext.translation() but also search inside ZIP archives

	if this module is loaded from one.
	"""

	archive = _get_archive()
	if (localedir is None or archive is None or
		not startswith_token(localedir, archive, os.sep)
	):
		return _gettext.translation(
			domain, localedir, languages, _class, fallback, codeset)

	if languages is None:
		languages = get_languages()
	languages = tuple(unique(filter(None, languages)))

	translations = None
	if languages:
		localedir = localedir[len(archive) + 1:].strip(os.sep)
		locale_suffix = os.path.join('LC_MESSAGES', domain + os.extsep + 'mo')
		with ZipFile(archive) as archive:
			#archive.debug = 3
			for lang in languages:
				lang_path = os.path.join(localedir, lang, locale_suffix)
				#print('Trying', lang_path, '...')
				translation_file = archive.open(lang_path,
					resolve_symlinks=True, fail_missing=False)
				if translation_file is not None:
					with translation_file:
						#print("Found language '{:s}' at '{:s}'.".format(lang, lang_path))
						translations = (
							(_class or GNUTranslations)(translation_file))
					break

	if translations is None:
		if not fallback:
			raise OSError(
				"No translation in '{:s}:{:s}' for: {:s}"
					.format(archive, localedir, ', '.join(languages)))
		translations = NullTranslations()
	if codeset is not None:
		translations.set_output_charset(codeset)

	return translations


def _get_gettext_shorthands(translations):
	last_error = None
	base_names = ('gettext', 'ngettext')
	for names in (map('u'.__add__, base_names), base_names):
		try:
			return operator.attrgetter(*names)(translations)
		except AttributeError as ex:
			last_error = ex
	raise last_error


def _make_translations():
	global _, _N, translations
	assert isinstance(translations, LazyInstance)
	translations = translation('messages', get_localedir(), fallback=True)
	_, _N = _get_gettext_shorthands(translations)
	return translations


translations = LazyInstance(_make_translations, NullTranslations, True)
_, _N = _get_gettext_shorthands(translations)
assert isinstance(translations, LazyInstance) and translations._li_instance is None


def _U(s):
	"""Don't translate (here) but mark string for translation anyway"""
	return s


class DictTranslations(NullTranslations):
	"""A simple Translations class based on a simple mapping object"""

	def __init__(self, _data=None, **kwargs):
		NullTranslations.__init__(self)

		if not _data:
			_data = kwargs
		elif kwargs:
			_data = _data.copy()
			_data.update(kwargs)
		self.data = _data


	def gettext(self, msg):
		translation = self.data.get(msg)
		if translation is not None:
			return translation
		return NullTranslations.gettext(self, msg)


	def ngettext(self, singular, plural, n):
		translation = self.data.get(singular if n == 1 else plural)
		if translation is not None:
			return translation
		return NullTranslations.ngettext(self, singular, plural, n)


	def lgettext(self, msg, *args):
		raise NotImplementedError

	lngettext = lgettext


	try:
		if NullTranslations.ugettext is not None:
			ugettext = gettext
		if NullTranslations.ungettext is not None:
			ungettext = ngettext
	except AttributeError:
		ugettext = None
		ungettext = None


try:
	_str_casefold = str.casefold
except AttributeError:
	_str_casefold = str.lower


def normalize_casefold(text):
	"""Normalize text data for caseless comparison

	Use the "canonical caseless match" algorithm defined in the Unicode Standard,
	version 10.0, section 3.13, requirement D146 (page 159).
	"""
	# Taken from https://stackoverflow.com/questions/319426/how-do-i-do-a-case-insensitive-string-comparison#comment60758553_29247821

	return unicodedata.normalize('NFKD',
		_str_casefold(unicodedata.normalize('NFKD',
			_str_casefold(unicodedata.normalize('NFD', text)))))


ChoiceInfo = collections.namedtuple('ChoiceInfo',
	('orig', 'translation', 'short', 'styled'))


class ChoiceHighlighters(
	collections.namedtuple('ChoiceHighlightersBase', ('shorthand', 'default'))
):

	unprintable_pattern = re.compile(r'｛｛(.*?)｝｝')


	@classmethod
	def from_termcaps(cls, shorthand_args, default_args):
		return cls(
			cls.from_termcap(*shorthand_args), cls.from_termcap(*default_args))


	@classmethod
	def from_termcap(cls, capname, default=None, flags_func=None):
		prefix = terminal.TERMMODES[capname]
		if prefix:
			suffix = terminal.TERMMODES['normal']
			if not suffix:
				raise RuntimeError(
					"Terminal supports '{:s}' but no way to revert to normal???"
						.format(capname))
			if '｝｝' in prefix or '｝｝' in suffix:
				raise ValueError("prefix or suffix contains illegal infix '｝｝'")
			highlighter = comp(
				fpartial(peek, cls._verify_unprintable_patterns),
				methodcaller(str.replace, suffix, suffix + prefix),
				fpartial('｛｛{0:s}｝｝{2:s}｛｛{1:s}｝｝'.format, prefix, suffix))

		elif isinstance(default, str):
			highlighter = default.format

		else:
			highlighter = default

		if flags_func is not None:
			highlighter = (highlighter, flags_func(prefix))

		return highlighter


	@classmethod
	def _verify_unprintable_patterns(cls, s):
		m = last(cls.unprintable_pattern.finditer(s), None)
		if m is not None and s.find('｛｛', m.end()) >= 0:
			raise ValueError("'{:s}' contains an unmatched infix '｛｛'.".format(s))


class Choices(collections.ChainMap):
	"""Display a set of options and ask for a choice among them."""

	default_highlighters = ChoiceHighlighters.from_termcaps(
		('underline', '[{:s}]'), ('bold', str.upper, bool))

	debug = False


	def __init__(self, *choices, **kwargs):
		"""Constructs a Choises object based on a set of options.

		The positional arguments must be (untranslated) strings yet their
		translations are used for display and shorthand selection.

		Keyword arguments:
		   * default - the default choice when the user enters nothing
		   * use_shorthand - Allow the use of a unique shorthand for each option.
		   * joiner - a string to display between options
		   * highlighters - a Highligters object with functions to transform the
		        default option and option shorthands to highlight them visually;
		        if stdout is a terminal defaults to bold and underling, otherwise
		        uppercase and brackets respectively.
		"""

		default = kwargs.pop('default', None)
		use_shorthands = kwargs.pop('use_shorthands', bool)
		joiner = kwargs.pop('joiner', '/')
		highlighters = kwargs.pop('highlighters', None)
		if kwargs:
			raise TypeError('Unexpected keyword arguments: ' + ', '.join(kwargs))

		if isinstance(default, int):
			default = choices[default]

		if not callable(use_shorthands):
			use_shorthands = getattr(use_shorthands, '__contains__', None) or bool

		if highlighters is None:
			highlighters = self.default_highlighters
		shorthand_highlighter, = (
			self._get_string_transformer(highlighters.shorthand))
		default_highlighter, default_highlighter_all = (
			self._get_string_transformer(highlighters.default, (False,)))

		self.orig = collections.OrderedDict()
		self.short = collections.OrderedDict()
		self.translations = collections.OrderedDict()
		self.default = None

		for orig in choices:
			is_default = orig == default
			translation = _(orig)
			if use_shorthands(orig):
				short, styled = self._get_short_and_styled(translation,
					shorthand_highlighter
						if not is_default or default_highlighter_all
						else functools.comp(shorthand_highlighter, default_highlighter),
					self.short)
			else:
				short = None
				styled = translation
			if is_default and default_highlighter_all:
				styled = default_highlighter(styled)

			c = ChoiceInfo(orig, translation, short, styled)

			if self.orig.setdefault(normalize_casefold(orig), c) is not c:
				raise ValueError("Duplicate choice '{:s}'".format(orig))
			if self.translations.setdefault(normalize_casefold(translation), c) is not c:
				raise ValueError(
					"Duplicate translation '{:s}' for choice '{:s}'"
						.format(translation, orig))
			if short is not None:
				assert short not in self.short
				self.short[short] = c
			if is_default:
				self.default = c

		if not self.orig:
			raise ValueError('No choices specified.')

		if default is not None and self.default is None:
			raise ValueError(
				"The default choice '{:s}' does not appear among the list of choices."
					.format(default))

		super(Choices, self).__init__(self.translations, self.short)

		self.joiner = joiner
		self.choices_string = joiner.join(
			map(operator.attrgetter('styled'), self.orig.values()))


	@staticmethod
	def _get_string_transformer(x, unpack_defaults=()):
		if not x:
			x = (identity,)
		if not isinstance(x, tuple):
			x = tuple(x) if isinstance(x, collections.Container) else (x,)
		if len(x) <= len(unpack_defaults):
			x += unpack_defaults[max(len(x) - 1, 0):]
		return x


	@staticmethod
	def _get_short_and_styled(s, shorthand_highlighter, existing):
		try:
			ishort, short = next(iter(
				ic for ic in enumerate(s) if ic[1] not in existing))
		except StopIteration:
			raise ValueError(
				"No unique shorthand available for choice '{:s}'".format(s))

		styled = s[:ishort] + shorthand_highlighter(short) + s[ishort + 1:]
		return normalize_casefold(short), styled


	def __str__(self):
		return self.choices_string


	def get_question(self, question, sep='  '):
		"""Construct a string combining a question and these choices"""
		return '{:s}{:s}({:s})'.format(question, sep, self.choices_string)


	def print_question(self, question, sep='  '):
		"""Print a question and these choices to stdout"""

		stdout = terminal.termwrap.stdout()
		write = stdout.file.write
		indent = stdout.subsequent_indent
		n = stdout.print(question, sep, True) % stdout.width
		i_last = len(self.orig) - 1
		debug = [] if self.debug else None

		# For each choice string see if it can fit on the current terminal line and
		# skip to the next line if not. Take care to not count escape sequences or
		# other unprintable characters.
		for i, c in enumerate(self.orig.values()):
			prefix = ('', '(')[not i]
			suffix = ')' if i == i_last else self.joiner
			unescaped = ChoiceHighlighters.unprintable_pattern.split(c.styled)
			printable_len = sum(map(len, islice(unescaped, 0, None, 2)))
			must_break = 0 <= stdout.width - len(indent) - printable_len < n
			if debug is not None:
				debug.append((i, n, printable_len, must_break,
					prefix + ''.join(islice(unescaped, 0, None, 2)) + suffix))
			if must_break:
				write('\n')
				write(indent)
				n = len(indent)
			write(prefix)
			stdout.file.writelines(unescaped)
			write(suffix)
			n = (n + printable_len) % stdout.width

		if debug is not None:
			print('\nWidth: {:d}'.format(stdout.width),
				*starmap(
					'Choice{:3d}: col={:3d}, len={:3d}, {!s:5s}, {!r}'.format, debug),
				sep='\n')

		return n


	def ask(self, question, sep='  ', *args, **kwargs):
		"""Print a question and choices and return an answer based on stdin.

		The answer string is resolved to a ChoiceInfo object, default, or None
		depending on the circumstances

		Additional positional and keyword arguments are passed to
		.terminal.try_input().
		"""

		self.print_question(question, sep)
		answer = terminal.try_input(None, *args, **kwargs)
		if isinstance(answer, str):
			answer = self.get(normalize_casefold(answer)) if answer else self.default
		return answer
