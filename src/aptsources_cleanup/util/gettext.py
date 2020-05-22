# -*- coding: utf-8

__all__ = (
	'translation', 'translations', '_', '_N', '_U',
	'NullTranslations', 'GNUTranslations', 'DictTranslations',
	'ChoiceInfo', 'Choices'
)

from . import terminal, collections
from .strings import startswith_token, prefix, strip, contains_ordered
from .operator import identity, methodcaller, peek, itemgetter0
from .itertools import unique, last, filterfalse
from .functools import LazyInstance, comp, partial as fpartial
from .zipfile import ZipFile
from .filesystem import dirseps
import gettext as _gettext
import operator
import sys
import os
import errno
import locale
import unicodedata
from itertools import islice, starmap, chain as ichain
from gettext import NullTranslations, GNUTranslations

try:
	import regex as re
except ImportError:
	import re


try:
	__archive__ = __loader__.archive
except AttributeError:
	__archive__ = None


def get_localedir(locales_subdir='share/locales'):
	src_root = os.path.dirname(os.path.dirname(
		__import__(prefix(__package__ or __name__, '.')).__file__))
	src_root_locales = os.path.join(src_root, locales_subdir)

	if __archive__ is None and not os.path.isdir(src_root_locales):
		src_root_parent_locales = os.path.join(
			os.path.dirname(src_root), locales_subdir)
		if os.path.isdir(src_root_parent_locales):
			return src_root_parent_locales

	return src_root_locales


def get_languages():
	langs = list(filter(None, ichain(
		(locale.getlocale(locale.LC_MESSAGES)[0],),
		os.environ.get('LANGUAGE', '').split(':'))))
	if not langs:
		langs.append('C')
	return langs


def get_fallback_languages(languages):
	"""Yields all supplied languages, each followed by their countryless fallback.

	Sometimes it is desirable to fall back to a language in its "global" form if
	a country-specific version is unavailable. This function takes an iterable of
	language code strings and returns a new iterable in which each supplied
	language, if it includes a country code, is immediately followed by a
	language code for the same language but _without_ country code.

	Examples:
		['en_US'] => ['en_US', 'en']
		['de_DE', 'fr_FR', 'en'] => ['de_DE', 'de', 'fr_FR', 'fr', 'en']
	"""

	for lang in filter(None, languages):
		yield lang
		p = lang.find('_')
		if p > 0:
			yield lang[:p]


def translation(domain, localedir=None, languages=None, _class=None,
	fallback=False, codeset=None
):
	"""Similar to gettext.translation() but also search inside ZIP archives

	if this module is loaded from one.
	"""

	if languages is None:
		languages = get_languages()

	archive = __archive__
	if (localedir is None or archive is None or
		not startswith_token(localedir, archive, os.sep)
	):
		return _gettext.translation(
			domain, localedir, languages, _class, fallback, codeset)

	languages = tuple(unique(get_fallback_languages(languages)))
	translations = None
	if languages:
		assert startswith_token(localedir, archive, dirseps)
		localedir = strip(localedir, dirseps, start=len(archive) + len(os.sep))
		locale_suffix = os.path.join('LC_MESSAGES', os.extsep.join((domain, 'mo')))
		with ZipFile(archive) as archive:
			#archive.debug = 3
			for lang in languages:
				lang_path = os.path.join(localedir, lang, locale_suffix)
				#print('Trying', lang_path, '...', file=sys.stderr)
				translation_file = archive.open(
					lang_path, follow_symlinks=True, fail_missing=False)
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


def _make_translations():
	global _, _N, translations
	assert isinstance(translations, LazyInstance)
	translations = translation('messages', get_localedir(), fallback=True)
	_ = translations.gettext
	_N = translations.ngettext
	return translations


translations = LazyInstance(_make_translations, NullTranslations, True)
_ = translations.gettext
_N = translations.ngettext
assert isinstance(translations, LazyInstance) and translations._li_instance is None


def _U(s):
	"""Don't translate (here) but mark string for translation anyway"""
	return s


class DictTranslations(NullTranslations):
	"""A simple Translations class based on a simple mapping object"""

	__slots__ = ('data',)


	def __init__(self, data=None, **kwargs):
		super().__init__()

		if data is None:
			data = kwargs
		elif kwargs:
			data.update(kwargs)
		self.data = data


	def gettext(self, msg):
		translation = self.data.get(msg)
		if translation is not None:
			return translation
		return super().gettext(msg)


	def ngettext(self, singular, plural, n):
		translation = self.data.get(singular if abs(n) == 1 else plural)
		if translation is not None:
			return translation
		return super().ngettext(singular, plural, n)


	def lgettext(self, msg, *args):
		raise NotImplementedError

	lngettext = lgettext


def normalize_casefold(text, *,
	_casefold=str.casefold, _normalize=unicodedata.normalize
):
	"""Normalize text data for caseless comparison

	Use the "canonical caseless match" algorithm defined in the Unicode Standard,
	version 10.0, section 3.13, requirement D146 (page 159).
	"""
	# Taken from https://stackoverflow.com/questions/319426/how-do-i-do-a-case-insensitive-string-comparison#comment60758553_29247821

	return _normalize('NFKD',
		_casefold(_normalize('NFKD',
			_casefold(_normalize('NFD', text)))))


ChoiceInfo = collections.namedtuple('ChoiceInfo',
	('orig', 'translation', 'short', 'styled'))


class ChoiceHighlighters(
	collections.namedtuple('ChoiceHighlightersBase', ('shorthand', 'default'))
):

	unprintable_delimiters = ("｛｛", "｝｝")

	assert (
		frozenset("()[]{}?*+-|^$\\.# \t\n\r\v\f")
			.isdisjoint(frozenset("".join(unprintable_delimiters)))), \
		'"unprintable_delimiters" contains regex meta-characters.'

	unprintable_pattern = re.compile(r"(.*?)".join(unprintable_delimiters))


	@classmethod
	def from_termcaps(cls, shorthand_args, default_args):
		return cls(*map(
			fpartial(cls._call_with_positional_or_keyword_args, cls.from_termcap),
			(shorthand_args, default_args)))


	@staticmethod
	def _call_with_positional_or_keyword_args(func, args):
		if isinstance(args, collections.abc.Mapping):
			return func(**args)
		return func(*args)


	@classmethod
	def from_termcap(cls, capname, default=None, flags_func=None):
		prefix = terminal.TERMMODES[capname]
		if prefix:
			suffix = terminal.TERMMODES['normal']
			if not suffix:
				raise AssertionError(
					"Terminal supports {!r} but no way to revert to normal???"
						.format(capname))
			if any(map(
				methodcaller(contains_ordered, cls.unprintable_delimiters),
				(prefix, suffix)
			)):
				raise ValueError(
					"Prefix ({!r}) or suffix ({!r}) contain illegal infix pair {!r}..{!r}"
						.format(prefix, suffix, *cls.unprintable_delimiters))
			highlighter = comp(
				cls._verify_unprintable_patterns,
				methodcaller(str.replace, suffix, suffix + prefix),
				fpartial("{d[0]}{prefix}{d[1]}{:s}{d[0]}{suffix}{d[1]}".format,
					prefix=prefix, suffix=suffix, d=cls.unprintable_delimiters))

		elif callable(default):
			highlighter = default

		else:
			try:
				highlighter = default.format
			except AttributeError:
				raise ValueError(
					"Unknown term mode {!r} and no valid default "
						"(got a {:s} instead of a str or bytes)"
						.format(capname, type(default).__qualname__))

		if flags_func is not None:
			highlighter = (highlighter, flags_func(prefix))

		return highlighter


	@classmethod
	def _verify_unprintable_patterns(cls, s):
		m = last(cls.unprintable_pattern.finditer(s), None)
		if m is not None and s.find(cls.unprintable_delimiters[0], m.end()) >= 0:
			raise ValueError(
				"{!r} contains an unmatched infix {!r}."
					.format(s, cls.unprintable_delimiters[0]))
		return s


class Choices(collections.ChainMap):
	"""Display a set of options and ask for a choice among them."""

	default_highlighters = ChoiceHighlighters.from_termcaps(
		('underline', '[{:s}]'), ('bold', str.upper, bool))

	debug = False


	def __init__(self, *choices, default=None, use_shorthands=None, joiner='/',
		highlighters=None
	):
		"""Constructs a Choices object based on a set of options.

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

		if isinstance(default, int):
			default = choices[default]

		if use_shorthands is None:
			use_shorthands = bool
		elif not callable(use_shorthands):
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
			translation = unicodedata.normalize('NFKC', _(orig))
			if use_shorthands(orig):
				short, styled = self._get_short_and_styled(translation,
					shorthand_highlighter
						if not is_default or default_highlighter_all
						else comp(shorthand_highlighter, default_highlighter),
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

		super().__init__(self.translations, self.short)

		self.joiner = joiner
		self.choices_string = joiner.join(tuple(
			map(operator.attrgetter('styled'), self.orig.values())))


	@staticmethod
	def _get_string_transformer(x, unpack_defaults=()):
		if not x:
			x = (identity,)
		elif not isinstance(x, tuple):
			x = tuple(x) if isinstance(x, collections.abc.Container) else (x,)
		if len(x) <= len(unpack_defaults):
			x += unpack_defaults[ max(len(x) - 1, 0): ]
		return x


	@classmethod
	def _get_short_and_styled(cls, s, shorthand_highlighter, existing):
		match = next(filterfalse(
			comp(operator.methodcaller('group'), existing.__contains__),
			cls.letter_pattern.finditer(s)), None)
		if match is None:
			raise ValueError(
				"No unique shorthand available for choice '{:s}'".format(s))

		short = match.group()
		styled = (
			shorthand_highlighter(short).join(
				(s[:match.start()], s[match.end():])))
		return (normalize_casefold(short), styled)


	# Try to detect grapheme clusters if supported
	letter_pattern = r'(?=\S)\X'
	try:
		letter_pattern = re.compile(letter_pattern, re.UNICODE)
	except re.error as ex:
		assert ex.pos - 1 <= letter_pattern.index(r'\X') <= ex.pos
		letter_pattern = None
	else:
		if not letter_pattern.match('A'):
			letter_pattern = None
	if letter_pattern is None:
		# Fall back to simple letter detection
		letter_pattern = re.compile(r'\S', re.UNICODE)
		if __debug__:
			terminal.termwrap.stderr().print(
				"Warning: The regular expression module '{:s}' of your Python "
				"installation lacks support for grapheme clusters.  If your language's "
				"script includes composed graphemes that do not correspond to a single "
				"Unicode codepoint the answer choice short-hands may behave "
				"unexpectedly.  Please install the 'regex' module to enable support "
				"for grapheme clusters.".format(re.__name__), '\n\n')


	def __str__(self):
		return self.choices_string


	def __repr__(self):
		return '{.__qualname__:s}([{:s}], default={!r}, joiner={!r})'.format(
			type(self), ', '.join(tuple(map(repr, self.orig.values()))),
			self.default and self.default.orig, self.joiner)


	def get_question(self, question, sep='  '):
		"""Construct a string combining a question and these choices"""
		return '{:s}{:s}({:s})'.format(question, sep, self.choices_string)


	def print_question(self, question, sep='  '):
		"""Print a question and these choices to stdout"""

		stdout = terminal.termwrap.stdout()
		write = stdout.file.write
		indent = stdout.subsequent_indent
		modulo_width = stdout.width.__rmod__ if stdout.width > 1 else identity
		n = modulo_width(stdout.print(question, sep, True))
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
			n = modulo_width(n + printable_len)

		if debug is not None:
			print(
				'\nWidth: {:d}'.format(stdout.width),
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
