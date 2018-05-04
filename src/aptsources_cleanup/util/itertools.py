def foreach(func, iterables):
def foreach(func, iterable):
	"""Call 'func' on each item in 'iterable'."""

	for x in iterable:
		func(x)
