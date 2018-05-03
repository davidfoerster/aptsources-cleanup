__all__ = ('identity', 'methodcaller')


def identity(x):
	return x


class methodcaller:

	__slots__ = ('func', 'args')


	def __init__(self, func, *args):
		self.func = func
		self.args = args


	def __call__(self, obj):
		return self.func(obj, *self.args)
