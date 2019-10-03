# -*- coding: utf-8
"""Detects and interactively deactivates duplicate Apt source entries and
deletes sources list files without valid enabled source entries in
'/etc/sources.list' and '/etc/sources.list.d/*.list'.


Author: David P. W. Foerster

Source code and bug tracker location:
  https://github.com/davidfoerster/aptsources-cleanup
"""


__all__ = ('get_duplicates', 'get_empty_files')

from . import util
from .util.filesystem import samefile
from .util.import_check import import_check
from .util.relations import EquivalenceRelation
from collections import defaultdict
from os.path import normpath
from urllib.parse import urlparse, urlunparse
aptsources = import_check('aptsources.sourceslist', 'apt')


from .util.version import get_version as __version__
__version__ = str(__version__())


def get_duplicates(sourceslist, equivalent_schemes=None):
	"""Detects and returns duplicate Apt source entries."""

	if equivalent_schemes is None:
		equivalent_schemes = EquivalenceRelation.EMPTY

	sentry_map = defaultdict(list)
	for se in sourceslist.list:
		if not se.invalid and not se.disabled:
			uri = urlparse(se.uri)
			scheme = equivalent_schemes.get_class(uri.scheme, uri.scheme)
			uri = urlunparse(uri._replace(scheme='', path=normpath(uri.path)))
			dist = normpath(se.dist)
			for c in (se.comps or (None,)):
				sentry_map[(se.type, scheme, uri, dist, c and normpath(c))].append(se)

	return filter(lambda dupe_set: len(dupe_set) > 1, sentry_map.values())


def get_empty_files(sourceslist):
	"""Detects source files without valid enabled entries.

	Returns pairs of file names and lists of their respective source entries.
	"""

	sentry_map = defaultdict(list)
	for se in sourceslist.list:
		sentry_map[se.file].append(se)

	return filter(
		lambda item: all(se.disabled | se.invalid for se in item[1]),
		sentry_map.items())
