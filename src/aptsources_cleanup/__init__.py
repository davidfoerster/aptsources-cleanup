# -*- coding: utf-8
"""Detects and interactively deactivates duplicate Apt source entries and
deletes sources list files without valid enabled source entries in
'/etc/sources.list' and '/etc/sources.list.d/*.list'.


Author: David P. W. Foerster

Source code and bug tracker location:
  https://github.com/davidfoerster/aptsources-cleanup
"""


__all__ = ('get_duplicates', 'get_empty_files')

from .util.import_check import import_check
from .util.relations import EquivalenceRelation
from collections import defaultdict
from os.path import normpath
from urllib.parse import urlparse
aptsources = import_check('aptsources.sourceslist', 'apt')


from .util.version import get_version as __version__
__version__ = str(__version__())


def get_duplicates(sourceslist, equivalent_schemes=EquivalenceRelation.EMPTY):
	"""Detects and returns duplicate Apt source entries."""

	if equivalent_schemes is None:
		equivalent_schemes = EquivalenceRelation.EMPTY

	sentry_map = defaultdict(list)
	for se in filter(is_valid, sourceslist.list):
		uri = se.parsed_uri = urlparse(se.uri, "file")
		uri = uri._replace(
			# Abuse the scheme attribute to store its equivalence class (if any)
			# which is fine as long as the result doesn't leak outside of this
			# function.
			scheme=equivalent_schemes.get_class(uri.scheme) or uri.scheme,
			path=normpath(uri.path))
		dist = normpath(se.dist)
		for component in (map(normpath, se.comps) if se.comps else (None,)):
			sentry_map[(se.type, uri, dist, component)].append(se)

	return filter(lambda dupe_set: len(dupe_set) > 1, sentry_map.values())


def get_empty_files(sourceslist):
	"""Detects source files without valid enabled entries.

	Returns pairs of file names and lists of their respective source entries.
	"""

	sentry_map = defaultdict(list)
	for se in sourceslist.list:
		sentry_map[se.file].append(se)

	return filter(
		lambda source_entries: not any(map(is_valid, source_entries)),
		sentry_map.values())


def is_valid(source_entry):
	return not (source_entry.invalid | source_entry.disabled)
