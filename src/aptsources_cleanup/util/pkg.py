# -*- coding: utf-8
"""Utility methods for DPKG package management"""
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ('check_integrity',)

from ._3to2 import *
from .gettext import _
from .io import FileDescriptor
import subprocess


def check_integrity(pkg, paragraphs, debug_fail=0):
	"""Check the integrity of an installed Apt package

	...based on its checksum file and warn about possible issues.
	"""

	md5sum_cmd = ('md5sum', '--check', '--strict', '--warn', '--quiet')
	md5sums_file = '/var/lib/dpkg/info/{:s}.md5sums'.format(pkg)

	try:
		md5sums_fd = FileDescriptor(md5sums_file)
		with md5sums_fd:
			md5sum_proc = subprocess.Popen(
				md5sum_cmd, cwd='/', stdin=md5sums_fd.fd, close_fds=True)
			try:
				md5sums_fd.close()
			finally:
				md5sum_proc.wait()
	except EnvironmentError as ex:
		paragraphs.append('{:s}: {:s}: {!s}'.format(
			_('Warning'), _('Cannot check package integrity'), ex))
		return False

	if md5sum_proc.returncode or debug_fail:
		paragraphs.append("{:s}: {:s}: {:s}: '{:s} < {:s}'".format(
			_('Warning'), _('Package integrity check failed'),
			_('exit status {status:d}').format(status=md5sum_proc.returncode),
			' '.join(md5sum_cmd), md5sums_file))

	return not (md5sum_proc.returncode or debug_fail)
