from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ('identity', 'methodcaller', 'starcall')


def identity(x):
	return x


class methodcaller:

	__slots__ = ('func', 'args')


	def __init__(self, func, *args):
		self.func = func
		self.args = args


	def __call__(self, obj):
		return self.func(obj, *self.args)


def starcall(func, args):
	return func(*args)
