#!/usr/bin/env python3
"""
Detects and interactively deactivates duplicate Apt source entries.

Usage: python3 apt-remove-duplicate-source-entries.py
"""

import aptsources.sourceslist

EMPTY_COMPONENT_LIST = (None,)

def get_duplicates(sourceslist):
	"""
	Detects and returns duplicate Apt source entries.
	"""

	sentry_map = dict()
	duplicates = list()
	for se in slist.list:
		if not se.invalid and not se.disabled:
			for c in (se.comps or EMPTY_COMPONENT_LIST):
				key = (se.type, se.uri, se.dist, c)
				previous_se = sentry_map.setdefault(key, se)
				if previous_se is not se:
					duplicates.append((se, previous_se))

	return duplicates


if __name__ == '__main__':
	slist = aptsources.sourceslist.SourcesList(False)
	duplicates = get_duplicates(slist)

	if duplicates:
		for dupe, orig in duplicates:
			print(
				('Overlapping source entries:\n  {0}: {1}\n  {2}: {3}\n' +
					'I disabled the latter entry.'
				).format(dupe.file, dupe, orig.file, orig))
			dupe.disabled = True

		print('\n{0} source entries were disabled:'.format(len(duplicates)),
			*[dupe for dupe, orig in duplicates], sep='\n  ', end='\n\n')
		if input('Do you want to save these changes? (y/N) ').upper() == 'Y':
			slist.save()
			
	else:
		print('No duplicated entries were found.')