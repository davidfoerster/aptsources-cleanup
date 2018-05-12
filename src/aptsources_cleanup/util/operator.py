# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ('identity', 'rapply', 'methodcaller', 'starcall')


def identity(x):
	"""Returns its attribute"""
	return x


def rapply(arg, func):
	"""Calls 'func(arg)' and returns its return value."""
	return func(arg)


class methodcaller(object):
	"""Binds arguments for instance(-like) method calls.

	Instance of this class are callable and pass their single positional argument
	as the first position argument to the wrapped function followed by the other
	arguments given during instantiation."""

	__slots__ = ('func', 'args')


	def __init__(self, func, *args):
		self.func = func
		self.args = args


	def __call__(self, obj):
		return self.func(obj, *self.args)


def starcall(func, args):
	"""Calls 'func' with variable arguments.

	Useful to create partial function objects that accept variadic arguments when
	used in contexts that don't expect it."""

	return func(*args)


def peek(func, arg0, *args):
	"""Calls func with the given arguments and returns _the first argument_."""
	func(arg0, *args)
	return arg0
