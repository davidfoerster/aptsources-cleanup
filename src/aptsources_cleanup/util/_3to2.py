from __future__ import \
	print_function, division, absolute_import, unicode_literals

try:
	from __builtin__ import \
		unicode as str, str as bytes, raw_input as input, xrange as range
except ImportError:
	pass

try:
	from future_builtins import *
except ImportError:
	pass
