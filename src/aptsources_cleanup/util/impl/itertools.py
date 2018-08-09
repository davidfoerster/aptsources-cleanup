from __future__ import print_function, division, absolute_import, unicode_literals
__all__ = ('accumulate',)
import operator


def accumulate(iterable, func=operator.add):
	'''Return running totals'''
	iterable = iter(iterable)
	accumulator = next(iterable)
	yield accumulator
	for element in iterable:
		accumulator = func(accumulator, element)
		yield accumulator
