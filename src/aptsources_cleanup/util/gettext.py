from __future__ import print_function, division, absolute_import, unicode_literals
from ._3to2 import *
from . import terminal
from . import functools
from . import collections
from .strings import startswith_token
from .operator import identity
from .itertools import unique
from .zipfile import ZipFile
import gettext as _gettext
import string
import operator
import itertools
import os
import os.path
import errno
import locale
import unicodedata


__all__ = (
	'translation', 'translations', '_', '_N', '_U', 'DictTranslations',
	'ChoiceInfo', 'Choices'
)


def get_localedir():
	return os.path.normpath(os.path.join(
		os.path.dirname(__file__), os.pardir, os.pardir, 'locales'))


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
	try:
		archive = __loader__.archive
	except AttributeError:
		archive = None

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
							(_class or _gettext.GNUTranslations)(translation_file))
					break

	if translations is None:
		if not fallback:
			raise OSError(
				"No translation in '{:s}:{:s}' for: {:s}"
					.format(archive, localedir, ', '.join(languages)))
		translations = _gettext.NullTranslations()
	if codeset is not None:
		translations.set_output_charset(codeset)

	return translations


translations = translation('messages', get_localedir(), fallback=True)

_ = translations.gettext
_N = translations.ngettext


def _U(s):
	"""Don't translate (here) but mark string for translation anyway"""
	return s


class DictTranslations(_gettext.NullTranslations):

	try:
		__base__
	except NameError:
		__base__ = _gettext.NullTranslations


	def __init__(self, _data=None, **kwargs):
		self.__base__.__init__(self)

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
		return self.__base__.gettext(self, msg)


	def ngettext(self, singular, plural, n):
		translation = self.data.get(singular if n == 1 else plural)
		if translation is not None:
			return translation
		return self.__base__.ngettext(self, singular, plural, n)


	def lgettext(self, msg, *args):
		raise NotImplementedError

	lngettext = lgettext


ChoiceInfo = collections.namedtuple('ChoiceInfo',
	('orig', 'translation', 'short', 'styled'))


def _highlighter_from_termcap(capname, default=None, flags_func=None):
	prefix = terminal.TERMMODES[capname]
	if prefix:
		suffix = terminal.TERMMODES['normal'] or None
		suffix_prefix = suffix + prefix
		highlighter = lambda s: prefix + s.replace(suffix, suffix_prefix) + suffix
	elif isinstance(default, str):
		highlighter = default.format
	else:
		highlighter = default

	if flags_func is not None:
		highlighter = (highlighter, flags_func(prefix))
	return highlighter


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


class Choices(collections.ChainMap):

	Highlighters = collections.namedtuple('Highlighters',
		('shorthand', 'default'))

	default_highlighters = Highlighters(
		_highlighter_from_termcap('underline', '[{:s}]'),
		_highlighter_from_termcap('bold', str.upper, bool)
	)


	def __init__(self, *choices, **kwargs):
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
			translation = translations.gettext(orig)
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
		return '{:s}{:s}({:s})'.format(question, sep, self.choices_string)


	_whitespace_del = dict.fromkeys(string.whitespace)
	del _whitespace_del[' ']


	def print_question(self, question, sep='  ', debug=False):
		stdout = terminal.termwrap.stdout()
		write = stdout.file.write
		indent = stdout.subsequent_indent
		n = stdout.print(question, sep, True) % stdout.width
		i_last = len(self.orig) - 1
		if debug:
			debug_data = []

		# For each choice string see if it can fit on the current terminal line and
		# skip to the next line if not. Take care to not count escape sequences or
		# other unprintable characters.
		for i, c in enumerate(self.orig.values()):
			prefix = ('', '(')[not i]
			suffix = ')' if i == i_last else self.joiner
			printable = terminal.termmodes_noctrl_pattern.sub('', c.styled)
			printable_len = len(prefix) + len(printable) + len(suffix)
			must_break = 0 <= stdout.width - len(indent) - printable_len < n
			if debug:
				debug_data.append(
					(i, n, printable_len, must_break, prefix + printable + suffix))
			if must_break:
				write('\n')
				write(indent)
				n = len(indent)
			write(prefix)
			write(c.styled.translate(self._whitespace_del))
			write(suffix)
			n = (n + printable_len) % stdout.width

		if debug:
			print('\nWidth: {:d}'.format(stdout.width),
				*itertools.starmap(
					'Choice{:3d}: col={:3d}, len={:3d}, {!s:5s}, {!r}'.format, debug),
				sep='\n')

		return n


	def ask(self, question, sep='  ', *args, **kwargs):
		self.print_question(question, sep)
		answer = terminal.try_input(None, *args, **kwargs)
		if isinstance(answer, str):
			answer = self.get(normalize_casefold(answer)) if answer else self.default
		return answer
