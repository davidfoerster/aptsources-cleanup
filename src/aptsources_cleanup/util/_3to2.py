from __future__ import print_function, division, absolute_import


try:
	from __builtin__ import \
		unicode as str, str as bytes, basestring, raw_input, \
		xrange as range

except ImportError:
	from builtins import input
	basestring = (str, bytes)

else:
	__all__ = tuple(map(bytes, __all__))

	import locale

	def input(prompt=None):
		answer = raw_input() if prompt is None else raw_input(prompt)
		return str(answer, locale.getpreferredencoding())


try:
	from future_builtins import *
except ImportError:
	pass
