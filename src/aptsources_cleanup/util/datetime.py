# -*- coding: utf-8
"""Like the eponymous built-in module but with additional back-ported
functonality if any.
"""
from __future__ import absolute_import, unicode_literals
from datetime import *


import datetime as _datetime
try:
	__all__ = _datetime.__all__
except AttributeError:
	from operator import methodcaller
	from .itertools import filterfalse
	__all__ = tuple(filterfalse(methodcaller('startswith', '_'), dir(_datetime)))


try:
	timezone
except NameError:
	from .impl.timezone import timezone
