from __future__ import print_function, division, absolute_import, unicode_literals
__all__ = ('accumulate',)
import operator


def accumulate(iterable, func=operator.add):
	'''Return running totals'''
	iterable = iter(iterable)
	total = next(iterable)
	yield total
	for element in iterable:
		total = func(total, element)
		yield total
