# -*- coding: utf-8
"""Like the eponymous built-in module but with additional back-ported
functonality if any.
"""
from __future__ import absolute_import, unicode_literals


import datetime as _datetime
try:
	__all__ = list(_datetime.__all__)
except AttributeError:
	from operator import methodcaller
	from .itertools import filterfalse
	__all__ = list(filterfalse(methodcaller('startswith', '_'), dir(_datetime)))


from datetime import *

if 'timezone' not in __all__:
	__all__.append('timezone')
	from .impl.timezone import timezone
