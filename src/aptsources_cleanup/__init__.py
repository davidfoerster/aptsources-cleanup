# -*- coding: utf-8
"""Detects and interactively deactivates duplicate Apt source entries and
deletes sources list files without valid enabled source entries in
'/etc/sources.list' and '/etc/sources.list.d/*.list'.


Author: David P. W. Foerster

Source code and bug tracker location:
  https://github.com/davidfoerster/aptsources-cleanup
"""

from __future__ import print_function, division, absolute_import
from . import util
from .util._3to2 import *
from .util.filesystem import samefile
from .util.import_check import import_check
import os.path
import collections
aptsources = import_check('aptsources.sourceslist', 'apt')

try:
	import urllib.parse
except ImportError:
	class urllib:
		import urlparse as parse


__all__ = ('get_duplicates', 'get_empty_files')

from .util.version import get_version as __version__
__version__ = str(__version__())


def get_duplicates(sourceslist):
	"""Detects and returns duplicate Apt source entries."""

	normpath = os.path.normpath
	urlparse = urllib.parse.urlparse
	urlunparse = urllib.parse.urlunparse

	sentry_map = collections.defaultdict(list)
	for se in sourceslist.list:
		if not se.invalid and not se.disabled:
			uri = urlparse(se.uri)
			uri = urlunparse(uri._replace(path=normpath(uri.path)))
			dist = normpath(se.dist)
			for c in (se.comps or (None,)):
				sentry_map[(se.type, uri, dist, c and normpath(c))].append(se)

	return filter(lambda dupe_set: len(dupe_set) > 1, sentry_map.values())


def get_empty_files(sourceslist):
	"""Detects source files without valid enabled entries.

	Returns pairs of file names and lists of their respective source entries.
	"""

	sentry_map = collections.defaultdict(list)
	for se in sourceslist.list:
		sentry_map[se.file].append(se)

	return filter(
		lambda item: all(se.disabled | se.invalid for se in item[1]),
		sentry_map.items())
