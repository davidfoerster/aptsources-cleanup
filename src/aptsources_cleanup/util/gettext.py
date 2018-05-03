from __future__ import print_function, division, absolute_import, unicode_literals
from ._3to2 import *
from . import terminal
from .operator import identity
import gettext as _gettext
import operator
import collections
import collections.abc
import os.path

__all__ = ('translation', '_', '_U', 'Choices', 'ChoiceInfo')


def get_localedir():
	return os.path.normpath(os.path.join(
		os.path.dirname(__file__), os.pardir, os.pardir, 'locales'))

print(*(_gettext.find('messages', get_localedir(), all=True) or (None,)), sep='\n', end='\n\n')
translation = _gettext.translation('messages', get_localedir(), fallback=True)
_ = translation.gettext


def _U(s):
	"""Don't translate (here) but mark string for translation anyway"""
	return s


ChoiceInfo = collections.namedtuple('ChoiceInfo',
	('orig', 'translation', 'short', 'styled'))


class Choices(collections.ChainMap):

	Highlighters = collections.namedtuple('Highlighters',
		('shorthand', 'default'))

	default_highlighters = Highlighters('[{:s}]'.format, (str.upper, False))


	def __init__(self, *choices, default=None, use_shorthands=bool, joiner='/',
		highlighters=None
	):
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
			translation = translation.gettext(orig)
			if use_shorthands(orig):
				short, styled = self._get_short_and_styled(translation,
					shorthand_highlighter
						if not is_default or default_highlighter_all
						else lambda s: default_highlighter(shorthand_highlighter(s)),
					self.short)
			else:
				short = None
				styled = translation
			if is_default and default_highlighter_all:
				styled = default_highlighter(styled)

			c = ChoiceInfo(orig, translation, short, styled)

			if self.orig.setdefault(orig.casefold(), c) is not c:
				raise ValueError("Duplicate choice '{:s}'".format(orig))
			if self.translations.setdefault(translation.casefold(), c) is not c:
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

		self.choices_string = joiner.join(
			map(operator.attrgetter('styled'), self.orig.values()))


	@staticmethod
	def _get_string_transformer(x, unpack_defaults=()):
		if not x:
			x = (identity,)
		if not isinstance(x, tuple):
			x = tuple(x) if isinstance(x, collections.abc.Container) else (x,)
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
		return short.casefold(), styled


	def __str__(self):
		return self.choices_string


	def get_question(self, question, sep=None):
		if sep is None: sep = '  '
		return '{:s}{:s}({:s})'.format(question, sep, self.choices_string)


	def ask(self, question, sep=None, *args, **kwargs):
		answer = terminal.try_input(
			self.get_question(question, sep), *args, **kwargs)
		if isinstance(answer, str):
			answer = self.get(answer.casefold()) if answer else self.default
		return answer
