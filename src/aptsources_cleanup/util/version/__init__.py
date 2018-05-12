# -*- coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals
from .._3to2 import *
import sys
import os.path
from .. import datetime
from itertools import starmap
from functools import partial as fpartial

__all__ = ('get_version', 'version_info')


class version_info(object):
	"""A version info object

	Attributes:
	  * version - an arbitrary version string
	  * commit - a string with a human-readable represenation of a revision
	       control system commit identifier
	  * date - a datetime.date (usually even datetime.datetime) instance
	  * branch_name - a name of the RCS branch used to build the denoted release
	       version

	All attributes are optional.
	"""

	__slots__ = ('version', 'date', 'commit', 'branch_name')


	def __init__(self, version, date=None, commit=None, branch_name=None):
		super(version_info, self).__init__()
		self.version = version
		self.date = date
		self.commit = commit
		self.branch_name = branch_name


	def items(self):
		"""Returns the attributes as a sequence of name-value tuples"""
		return zip(self.__slots__, map(fpartial(getattr, self), self.__slots__))


	def __repr__(self):
		return '{:s}.{:s}({:s})'.format(
			self.__class__.__module__, self.__class__.__qualname__,
			', '.join(starmap('{:s}={!r}'.format, self.items())))


	def __str__(self):
		v = [str(self.version)]

		if self.date:
			if isinstance(self.date, datetime.date):
				v.append(self.date.strftime('%Y-%m-%d'))
			else:
				v.append(self.date)

		if self.commit:
			v.append(self.commit[:7])
			if self.branch_name:
				v[-1] += ':' + self.branch_name

		return ' '.join(v)


	@classmethod
	def load(cls):
		"""Load a version object from environment information.

		Tries to load or construct version information based on the environment in
		the following order:

		 1. using the attributes of the ._data module (relative to this module),
		 2. the first line of the 'VERSION' file located two directory levels above
		    the module search path root for this module or package for the 'version'
		    attribute only,
		 3. from 'from_repo(version)'.
		"""
		try:
			from . import _data
		except ImportError:
			pass
		else:
			return cls(
				*map(fpartial(getattr, _data), cls.__slots__))

		try:
			f = open(os.path.join(
				os.path.dirname(os.path.dirname(os.path.dirname(
					sys.modules[(__package__ or __name__).partition('.')[0]].__file__))),
				'VERSION'))
			with f:
				version = f.readline(1<<10)
		except FileNotFoundError:
			version = None
		else:
			version = str(version).strip()

		return cls.from_repo(version)


	@classmethod
	def from_repo(cls, version=None, repo_dir=None):
		"""Construct a version_info using the current state of a Git repository"""

		import git
		try:
			repo = git.Repo(repo_dir)
		except git.exc.InvalidGitRepositoryError:
			return cls(version)

		commit = repo.commit()
		branch = next((h.name for h in repo.heads if h.commit == commit), None)

		try:
			date = commit.committed_datetime
		except AttributeError:
			date = None
		else:
			date = date.astimezone(datetime.timezone(date.utcoffset()))

		return cls(version, date, commit.hexsha, branch)


	_data_module_header = (
'''from __future__ import absolute_import, unicode_literals
from .. import datetime
''')


	def _print_data_module(self, file=None):
		if file is None:
			file = sys.stdout
		print(
			'# -*- coding: ' + file.encoding,
			self._data_module_header,
			*starmap('{:s} = {!r}'.format, self.items()),
			sep='\n', file=file)


_version = None

def get_version():
	"""Return the current version info.

	The first call to this function will call version_info.load() and cache the
	result for later calls.
	"""

	global _version
	if _version is None:
		_version = version_info.load()
	return _version


def _if_bytes_to_str(obj, *encoding):
	return obj.decode(*encoding) if isinstance(obj, bytes) else obj
