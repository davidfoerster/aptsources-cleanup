# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = (
	'comp', 'cmp_to_key', 'total_ordering', 'reduce', 'update_wrapper', 'wraps',
	'partial', 'LazyInstance'
)

from ._3to2 import *
from functools import *
from .operator import rapply, identity


def comp(*funcs):
	if len(funcs) <= 1:
		return funcs[0] if funcs else identity
	return partial(reduce, rapply, funcs)


class LazyInstance(object):

	__slots__ = ('_li_instance', '_li_factory', '_li_type_hint', '_li_strict')


	def __init__(self, factory, type_hint=None, strict=False):
		self._li_instance = None
		self._li_factory = factory
		self._li_strict = strict

		if type_hint is None:
			if isinstance(factory, TypesType):
				type_hint = factory
		elif not isinstance(type_hint, TypesType):
			raise TypeError(
				'type_hint must be None or a type, not ' + str(type(type_hint)))
		self._li_type_hint = type_hint


	@property
	def _instance(self):
		if self._li_factory is not None:
			self._li_instance = self._li_factory()
			assert (self._li_type_hint is None or
				isinstance(self._li_instance, self._li_type_hint))
			self._li_factory = None
			self._li_type_hint = None

		return self._li_instance


	def __getattr__(self, name):
		if self._li_type_hint is not None:
			if self._li_strict:
				value = getattr(self._li_type_hint, name)
			else:
				value = getattr(self._li_type_hint, name, None)
			if callable(value):
				return self._li_bind_method_impl(name)

		return getattr(self._instance, name)


	def _bind_method(self, *methods_or_names):
		if len(methods_or_names) == 1:
			return self._li_bind_method_impl(methods_or_names)
		return map(self._li_bind_method_impl, methods_or_names)


	def _li_bind_method_impl(self, method_or_name):
		if self._li_factory is None:
			if callable(method_or_name):
				return method_or_name(self._li_instance)
			return getattr(self._li_instance, name)

		if callable(method_or_name):
			def bound_method(*args, **kwargs):
				return method_or_name(self._instance)(*args, **kwargs)

		else:
			def bound_method(*args, **kwargs):
				return getattr(self._instance, method_or_name)(*args, **kwargs)

		return bound_method
