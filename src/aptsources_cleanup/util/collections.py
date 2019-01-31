# -*- coding: utf-8
"""Like the eponymous built-in module but with additional back-ported
functonality if any.
"""
from collections import *


class ExtSet(set):

	def add(self, x):
		l = len(self)
		super().add(x)
		return l != len(self)
