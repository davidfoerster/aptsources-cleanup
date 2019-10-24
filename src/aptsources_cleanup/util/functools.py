# -*- coding: utf-8
"""Utilities for and around functional programming"""

__all__ = ['comp', 'LazyInstance']

from functools import *
import functools as _functools
__all__ += _functools.__all__

from  operator import attrgetter
from .operator import identity


class comp:
	"""A function object that concatenates the passed functions from left to
	right.
	"""

	__slots__ = ('funcs',)


	def __new__(cls, *funcs):
		if len(funcs) <= 1:
			return funcs[0] if funcs else identity
		return super().__new__(cls)


	def __init__(self, *funcs):
		assert all(map(callable, funcs))
		self.funcs = funcs


	def __call__(self, *args):
		funcs = self.funcs
		if funcs:
			funcs = iter(funcs)
			args = next(funcs)(*args)
			for f in funcs:
				args = f(args)
		else:
			args, = args
		return args


class LazyInstance:
	"""Instantiate objects lazily on first access

	Instances of this class provide transparent attribute access to the wrapped
	instance which is created on demand during the first access or on first call
	for methods present in the type of the wrapped object (if known).
	"""

	__slots__ = ('_li_instance', '_li_factory', '_li_type_hint', '_li_strict')


	def __init__(self, factory, type_hint=None, strict=False):
		"""Creates a new lazy instance object

		'factory' must be a nullary function that returns the underlying object as
		needed and is called at most once.

		'type_hint' is a hint to the type of the return value of 'factory'. If
		unset or None and if 'factory' is itself a type it defaults to 'factory'.
		A type hint is necessary for implicit lazy instantion on method call.

		If 'strict' is true and a type hint is available (see above) raise
		AttributeError when trying to access attributes that exist neither on
		LazyInstance nor on the type of the (future) wrapped object.
		"""

		self._li_instance = None
		self._li_factory = factory
		self._li_strict = strict

		if type_hint is None:
			if isinstance(factory, type):
				type_hint = factory
		elif not isinstance(type_hint, type):
			raise TypeError(
				'type_hint must be None or a type, not ' + str(type(type_hint)))
		self._li_type_hint = type_hint


	__hash__ = None


	def _get_instance(self):
		"""Accesses the wrapped instance

		and create it using the factory method provided earlier if necessary.
		"""

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

		return getattr(self._get_instance(), name)


	def _bind_method(self, *methods_or_names):
		"""Wrap a lazy method call

		Returns a function based on an attribute of the (future) wrapped object but
		don't instantiate the wrapped object until execution.  You can provide both
		attribute names or an arbitrary getter method for attribute access.

		If you specify multible accessors this returns a sequence of functions as
		described above.
		"""

		if len(methods_or_names) == 1:
			return self._li_bind_method_impl(*methods_or_names)
		return map(self._li_bind_method_impl, methods_or_names)


	def _li_bind_method_impl(self, method_or_name):
		if callable(method_or_name):
			getter = method_or_name
			if self._li_factory is None:
				return getter(self._li_instance)
		else:
			if self._li_factory is None:
				return getattr(self._li_instance, method_or_name)
			getter = attrgetter(method_or_name)

		return lambda *args: getter(self._get_instance())(*args)
