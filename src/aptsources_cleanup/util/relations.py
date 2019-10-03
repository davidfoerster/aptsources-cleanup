# -*- coding: utf-8
__all__ = ('EquivalenceRelation',)

import itertools
from operator import methodcaller
from functools import partial as fpartial


class EquivalenceRelation(frozenset):

	def __new__(cls, *classes):
		if len(classes) == 1:
			classes, = classes
		er = super().__new__(cls, map(frozenset, classes))

		if __debug__:
			overlapping = [
				'{!r} ⋂ {!r} = {!r}'.format(set(a), set(b), set(a & b))
				for a, b in itertools.combinations(er, 2) if not a.isdisjoint(b)
			]
			if overlapping:
				raise AssertionError(
					'Overlapping equivalence classes: ' + ', '.join(overlapping))

		return er


	def get_class(self, element, default=None):
		for clazz in self:
			if element in clazz:
				return clazz
		return default


	@classmethod
	def parse(cls, s, item_delimiter=',', class_delimiter=';'):
		return cls(map(
			methodcaller('split', item_delimiter), s.split(class_delimiter)))


	def __format__(self, fmt):
		classes = self

		if fmt:
			fmt_orig = fmt
			fmt = fmt[1:].split(fmt[0])
			if len(fmt) % 2:
				classes, item_transform = (
					self._format_parse_options(fmt.pop(), classes))
			else:
				item_transform = None
			if len(fmt) == 6:
				prefix_suffix = fmt[4:]
				del fmt[4:]
			else:
				prefix_suffix = ('', '')
			if len(fmt) == 4:
				class_prefix_suffix = fmt[2:]
				del fmt[2:]
			else:
				class_prefix_suffix = ('', '')
			if len(fmt) == 2:
				class_delimiter = fmt.pop()
				item_delimiter = fmt.pop()
			else:
				raise ValueError('Illegal format: ' + repr(fmt_orig))

		else:
			item_delimiter = ', '
			class_delimiter = '; '
			item_transform = repr
			prefix_suffix = class_prefix_suffix = ('{', '}')

		if item_transform is not None:
			classes = map(fpartial(map, item_transform), classes)

		s = class_delimiter.join(tuple(
			map(methodcaller('join', class_prefix_suffix),
				map(item_delimiter.join, classes))))
		return s.join(prefix_suffix)


	@classmethod
	def _format_parse_options(cls, s, classes):
		opts = set(s)

		try:
			sort_mode = next(filter(opts.__contains__, ('a', 'd')), None)
			if sort_mode is not None:
				opts.remove(sort_mode)
				classes = sorted(classes, reverse=sort_mode == 'd')

			if opts:
				item_transform, = opts
			else:
				item_transform = ''
			item_transform = cls._item_transformers[item_transform]

		except (TypeError, KeyError):
			raise ValueError('Invalid format option string: ' + repr(s))

		return (classes, item_transform)


	_item_transformers = { '': None, 's': str, 'r': repr }


EquivalenceRelation.EMPTY = EquivalenceRelation()


class IndexedEquivalenceRelation(EquivalenceRelation):

	__slots__ = ('_index',)


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._index = dict(itertools.chain.from_iterable(
			zip(clazz, itertools.repeat(clazz)) for clazz in self))


	def get_class(self, element, default=None):
		return self._index.get(element, default)
