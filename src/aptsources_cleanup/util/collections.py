# -*- coding: utf-8
from __future__ import absolute_import
from collections import *

import collections as _collections
__all__ = _collections.__all__


try:
	ChainMap
except NameError:
	from .impl.chainmap import ChainMap
