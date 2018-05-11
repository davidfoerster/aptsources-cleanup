# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ('identity', 'rapply', 'methodcaller', 'starcall')


def identity(x):
	return x


def rapply(arg, func):
	return func(arg)


class methodcaller(object):

	__slots__ = ('func', 'args')


	def __init__(self, func, *args):
		self.func = func
		self.args = args


	def __call__(self, obj):
		return self.func(obj, *self.args)


def starcall(func, args):
	return func(*args)


def peek(func, arg0, *args):
	func(arg0, *args)
	return arg0
