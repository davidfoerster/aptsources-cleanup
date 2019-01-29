# -*- coding: utf-8

__all__ = ('import_check',)

from . import pkg
from .gettext import _
from .terminal import termwrap
from .filesystem import samefile
import sys


def import_check(module_name, apt_pkg_suffix, import_error=None, debug_fail=0):
	"""Check for possible issues during the import of the given module

	...and print warnings as appropriate.
	"""

	if import_error is None or debug_fail > 0:
		try:
			module = __import__(module_name)
			if debug_fail > 0:
				import __nonexistant_module__ as module
				raise AssertionError
		except ImportError as ex:
			import_error = ex
		else:
			return module

	python_name = 'python'
	if sys.version_info.major >= 3:
		python_name += str(sys.version_info.major)
	python_exe = '/usr/bin/' + python_name
	python_pkg = python_name + '-minimal'
	apt_pkg = '-'.join((python_name, apt_pkg_suffix))

	paragraphs = [
		'{:s}: {!s}.  {:s}  {:s}'.format(
			type(import_error).__name__, import_error,
			_("Do you have the '{package:s}' package installed?  You can do so with:")
				.format(package=apt_pkg),
			apt_pkg)
	]

	if not samefile(python_exe, sys.executable) or debug_fail:
		questional_interpreter_msg = len(paragraphs)
		paragraphs.append(': '.join((
			_('Warning'),
			_("The current Python interpreter is '{py_exe:s}'.  Please use the "
					"default '{py_exe_default:s}' if you encounter issues with the "
					"import of the '{module:s}' module.")
				.format(py_exe=sys.executable, py_exe_default=python_exe,
					module=module_name))))
	else:
		questional_interpreter_msg = None

	if not pkg.check_integrity(python_pkg, paragraphs, debug_fail):
		msg = (
			_("Please make sure that the '{package:s}' package wasn't corrupted and "
					"that '{py_exe:s}' refers to the Python interpreter from the same "
					"package.")
				.format(package=python_pkg, py_exe=python_exe))
		if questional_interpreter_msg is not None:
			paragraphs[questional_interpreter_msg] = '  '.join((
				paragraphs[questional_interpreter_msg], msg))
		else:
			paragraphs.append(': '.join((_('Warning'), msg)))

	try:
		termwrap.get(sys.stderr, ignore_errors=False)
	except EnvironmentError as ex:
		print(_('Warning'),
			_('Cannot wrap text output due a failure to get the terminal size'),
			ex, sep=': ', end='\n\n', file=sys.stderr)

	termwrap.stderr().print_all(paragraphs)
	sys.exit(127)
