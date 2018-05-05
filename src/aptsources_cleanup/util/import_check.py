from __future__ import print_function, division, absolute_import, unicode_literals
from ._3to2 import *
from . import pkg
from .gettext import _
from .terminal import termwrap
from .filesystem import samefile
import sys
import importlib

__all__ = ('import_check',)


def import_check(py_module, apt_pkg_suffix, import_error=None, debug_fail=0):
	"""Check for possible issues during the import of the given module

	...and print warnings as appropriate.
	"""

	if import_error is None or debug_fail > 0:
		try:
			aptsources = importlib.import_module(py_module)
			if debug_fail > 0:
				import __nonexistant_module__ as aptsources
				raise AssertionError
		except ImportError as ex:
			import_error = ex
		else:
			return aptsources

	python_name = 'python'
	if sys.version_info.major >= 3:
		python_name += str(sys.version_info.major)
	python_exe = '/usr/bin/' + python_name
	python_pkg = python_name + '-minimal'
	apt_pkg = python_name + '-' + apt_pkg_suffix

	paragraphs = [
		'{:s}: {!s}.  {:s}  {:s}'.format(
			type(import_error).__name__, import_error,
			_("Do you have the '{:s}' package installed?  You can do so with:")
				.format(apt_pkg),
			apt_pkg)
	]

	questional_interpreter = (
		not samefile(python_exe, sys.executable) or debug_fail)
	if questional_interpreter:
		paragraphs.append(_('Warning') + ': ' +
			_("The current Python interpreter is '{:s}'.  Please use the default '{:s}' if you encounter issues with the import of the '{:s}' module.")
				.format(sys.executable, python_exe, py_module))

	if not pkg.check_integrity(python_pkg, paragraphs, debug_fail):
		msg = (
			_("Please make sure that the '{:s}' package wasn't corrupted and that '{:s}' refers to the Python interpreter from the same package.")
					.format(python_pkg, python_exe))
		if questional_interpreter:
			paragraphs[-1] += '  ' + msg
		else:
			paragraphs.append(_('Warning') + ': ' + msg)

	try:
		termwrap.get(sys.stderr, ignore_errors=False)
	except EnvironmentError as ex:
		print(_('Warning'),
			_('Cannot wrap text output due a failure to get the terminal size'),
			ex, sep=': ', end='\n\n', file=sys.stderr)

	termwrap.stderr().print_all(paragraphs)
	sys.exit(127)
