# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals
from ._3to2 import *
from functools import *
from .operator import rapply, identity

__all__ = (
	'comp', 'cmp_to_key', 'total_ordering', 'reduce', 'update_wrapper', 'wraps',
	'partial', 'lazy'
)


def comp(*funcs):
	if len(funcs) <= 1:
		return funcs[0] if funcs else identity
	return partial(reduce, rapply, funcs)


class lazy(object):

	__slots__ = ('_wrapped_instance', '_wrapped_ctor', '_attrgetters')


	def __init__(self, wrapped_ctor, **attrgetters):
		self._wrapped_instance = None
		self._wrapped_ctor = wrapped_ctor
		self._attrgetters = attrgetters


	@property
	def wrapped_instance(self):
		if self._wrapped_ctor is not None:
			self._wrapped_instance = self._wrapped_ctor()
			self._wrapped_ctor = None
		return self._wrapped_instance


	def __getattr__(self, name):
		getter = self._attrgetters.get(name)
		if getter is not None:
			return getter(self.wrapped_instance)
		return getattr(self.wrapped_instance, name)


	def _bind_method(self, *methods):
		if len(methods) == 1:
			return self._bind_method_impl(method)
		return map(self._bind_method_impl, methods)


	def _bind_method_impl(self, method):
		if not callable(method):
			method = partial(getattr, self, method)

		def bound_method(*args, **kwargs):
			return method(self.wrapped_instance)(*args, **kwargs)

		return bound_method
