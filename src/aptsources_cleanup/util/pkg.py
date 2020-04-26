# -*- coding: utf-8
"""Utility methods for DPKG package management"""

__all__ = ('check_integrity',)

from .gettext import _
from .io import FileDescriptor
import subprocess


def check_integrity(pkg, paragraphs, debug_fail=0, *,
	md5sum_cmd = ('md5sum', '--check', '--strict', '--warn', '--quiet')
):
	"""Check the integrity of an installed Apt package

	...based on its checksum file and warn about possible issues.
	"""

	md5sums_file = '/var/lib/dpkg/info/{:s}.md5sums'.format(pkg)

	try:
		with FileDescriptor(md5sums_file) as md5sums_fd:
			if isinstance(md5sums_fd, int):
				raise EnvironmentError(
					'Got error code {} when opening {}'.format(md5sums_fd, md5sums_file))
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
