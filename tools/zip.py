#!/usr/bin/python3 -O
# -*- coding: utf-8

"""Create (executable Python) ZIP archives"""

__all__ = ("ZipFile",)

import io
import os
import sys
import stat
import time
import errno
import zipfile
import argparse
import operator
import itertools
import contextlib
import collections
from argparse import _, ngettext as _N
from functools import partial as fpartial
if __debug__:
	import traceback

import zlib
try:
	import bz2
except ImportError:
	bz2 = None
try:
	import lzma
except ImportError:
	lzma = None


itemgetter0 = operator.itemgetter(0)


def identity(x):
	return x


class ZipInfo(zipfile.ZipInfo):

	__slots__ = ("compress_options",)


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.compress_options = None


	@classmethod
	def from_file(cls, filename, arcname=None):
		if isinstance(arcname, ZipInfo):
			# Monkey patch to pass through ZipInfo objects where ZipFile methods
			# expect plain names.
			try:
				# Unwrap compression options if necessary
				arcname.compress_type, arcname.compress_options = arcname.compress_type
			except TypeError:
				pass
			return arcname

		return super().from_file(filename, arcname)

zipfile.ZipInfo = ZipInfo


if lzma is not None:
	import struct

	class LZMACompressor(zipfile.LZMACompressor):
		# Monkey patch to pass compressor options through

		__slots__ = ("compress_options",)


		def __init__(self, preset=None, compress_options=None):
			super().__init__()

			if compress_options is None:
				compress_options = {}
			if (compress_options.setdefault("id", lzma.FILTER_LZMA1)
				!= lzma.FILTER_LZMA1
			):
				raise ValueError(
					"Illegal LZMA filter ID: " + repr(compress_options["id"]))
			if preset is not None:
				compress_options["preset"] = preset
			self.compress_options = compress_options


		def _init(self):
			props = lzma._encode_filter_properties(self.compress_options)
			self._comp = lzma.LZMACompressor(
				lzma.FORMAT_RAW,
				filters=(
					lzma._decode_filter_properties(self.compress_options["id"], props),))
			return struct.pack("<BBH", 9, 4, len(props)) + props

	zipfile.LZMACompressor = LZMACompressor


class _ZipWriteFile(zipfile._ZipWriteFile):
	# Monkey patch to pass compressor options through

	__slots__ = ()

	_get_compressor_orig = staticmethod(zipfile._get_compressor)

	_compressor_ctors = {
		zipfile.ZIP_STORED: None,
		zipfile.ZIP_DEFLATED: fpartial(
			zlib.compressobj, method=zlib.DEFLATED, wbits=-15),
		zipfile.ZIP_BZIP2: NotImplemented if bz2 is None else bz2.BZ2Compressor,
		zipfile.ZIP_LZMA: NotImplemented if lzma is None else LZMACompressor,
	}


	def __init__(self, zf, zinfo, zip64):
		super().__init__(zf, zinfo, zip64)
		self._compressor = self._get_compressor(
			zinfo.compress_type, zinfo.compress_options)


	@classmethod
	def _get_compressor(cls, compress_type, compress_options):
		compressor = cls._compressor_ctors.get(compress_type, NotImplemented)

		if compressor is None:
			return None

		if compressor is NotImplemented:
			try:
				compress_type = ("Unsupported", zipfile.compressor_names[compress_type])
			except KeyError:
				compress_type = ("Unknown", repr(compress_type))
			raise ValueError(" compression type: ".join(compress_type))

		if compress_options is None:
			return compressor()
		args, kwargs = compress_options
		if args is None:
			args = ()
		if kwargs is None:
			return compressor(*args)
		return compressor(*args, **kwargs)

zipfile._ZipWriteFile = _ZipWriteFile
zipfile._get_compressor = identity


class ZipFile(zipfile.ZipFile):
	"""Like zipfile.ZipFile"""

	__slots__ = ("compress_options",)

	compression_level_max = 9

	compression_size_threshold = 256

	compressor_ids = dict(
		map(operator.itemgetter(1, 0), zipfile.compressor_names.items()))

	supported_compressors = [
		zipfile.compressor_names[id]
			for id, ctor in _ZipWriteFile._compressor_ctors.items()
			if ctor is not NotImplemented
	]


	def __init__(self, *args, compress_options=None, **kwargs):
		super().__init__(*args, **kwargs)
		self.compress_options = self._parse_compress_options(
			compress_options, self.compression)


	@staticmethod
	def _parse_compress_options(opt, type=None):
		if opt is not None:
			if type == zipfile.ZIP_STORED:
				opt = None
			elif isinstance(opt, int):
				opt = ((opt,), None) if opt >= 0 else None
		return opt


	def write(self, filename_or_fd, arcname=None, compress_type=None, *,
		compress_options=None, dir_fd=None, follow_symlinks=True,
		_default_open_flags=os.O_RDONLY | os.O_CLOEXEC
	):
		"""Adds a file to this archive.

		Like zipfile.ZipFile.write() with the following additions:

		 - "filename_or_fd" may be an int that represents an open file descriptor.
		 - Supports a "dir_fd" argument.
		 - Supports symbolic links.
		"""

		if arcname is None:
			arcname = os.fspath(filename_or_fd)

		if isinstance(filename_or_fd, int):
			open_flags = 0
			fd = filename_or_fd
		else:
			open_flags = _default_open_flags
			if not follow_symlinks:
				open_flags |= os.O_NOFOLLOW
			try:
				fd = os.open(filename_or_fd, open_flags, dir_fd=dir_fd)
			except OSError as ex:
				if not (ex.errno == errno.ELOOP and open_flags & os.O_NOFOLLOW):
					raise
				open_flags |= os.O_PATH
				fd = os.open(filename_or_fd, open_flags, dir_fd=dir_fd)

		fd = FileDescriptor(fd)
		with fd:
			fd_stat = os.fstat(fd.fd)

			if compress_type is not None:
				compress_options = self._parse_compress_options(
					compress_options, compress_type)
			elif (stat.S_ISDIR(fd_stat.st_mode) or
				fd_stat.st_size < self.compression_size_threshold
			):
				compress_type = zipfile.ZIP_STORED
				compress_options = None
			else:
				compress_type = self.compression
				compress_options = self.compress_options

			if stat.S_ISLNK(fd_stat.st_mode):
				target = os.readlink(b"", dir_fd=fd.fd)
				fd.close()
				info = zipfile.ZipInfo(arcname, time.localtime(fd_stat.st_mtime))
				info.external_attr |= (fd_stat.st_mode & 0xFFFF) << 16
				info.compress_type = compress_type
				info.compress_options = compress_options
				self.writestr(info, target, compress_type)
			else:
				assert not open_flags & os.O_PATH
				info = zipfile.ZipInfo.from_file(fd.fd, arcname)
				info.compress_type = compress_type
				info.compress_options = compress_options
				super().write(fd.release(), info, compress_type)

		return info


class FileDescriptor(contextlib.AbstractContextManager):
	"""A context manager for operating system file descriptors"""

	__slots__ = ('_fd',)


	def __init__(self, path, flags=os.O_RDONLY, mode=0o777, *, dir_fd=None):
		if isinstance(path, int):
			self._fd = path
		else:
			self._fd = os.open(path, flags, mode, dir_fd=dir_fd)


	@property
	def fd(self):
		if self._fd is None:
			raise RuntimeError(
				"This file descriptor was closed or released earlier.")
		return self._fd


	def close(self):
		"""Close the underlying file descriptor."""

		if self._fd is not None:
			os.close(self._fd)
			self._fd = None


	@property
	def closed(self):
		return self._fd is None


	def release(self):
		"""Release and return the underlying file descriptor."""

		fd = self.fd
		self._fd = None
		return fd


	def __enter__(self):
		return self.fd


	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()


def attrs2dict(src, dst, attrnames, omit_value=None):
	for name in attrnames:
		value = getattr(src, name, omit_value)
		if value is not omit_value:
			dst[name] = value


class itercontextmanager:

	def __init__(self, generator):
		self.generator = generator
		attrs2dict(
			generator, self.__dict__, ("__name__", "__qualname__", "__doc__"))


	def __call__(self, *args, **kwargs):
		with contextlib.ExitStack() as exitstack:
			generator = self.generator(*args, _exitstack=exitstack, **kwargs)
			del args, kwargs
			yield from generator


	def __repr__(self):
		return "{:s}({!r})".format(self.__class__.__qualname__, self.generator)


	def __str__(self):
		return "<{:s} of {:s}>".format(
			self.__class__.__qualname__,
			getattr(self.generator, "__qualname__", None) or repr(self.generator))


@itercontextmanager
def getlines(stream, delim, chunk_size=0, *, _exitstack):
	assert isinstance(chunk_size, int)
	assert isinstance(_exitstack, contextlib.ExitStack)

	if chunk_size <= 0:
		if chunk_size:
			raise ValueError("Non-positive chunk size " + format(chunk_size, "n"))
		chunk_size = 1 << 20

	if isinstance(stream, io.TextIOBase):
		delim_alt = (None, "\n")[ delim == stream.newlines != "" ]
	elif isinstance(stream, io.IOBase):
		delim_alt = (None, b"\n")[ delim == b"\n" ]
	else:
		delim_alt = None

	if delim_alt is not None:
		return map(operator.methodcaller("rstrip", delim_alt), stream)

	if isinstance(delim, collections.abc.ByteString):
		return _getlines_impl_bytes(stream, delim, chunk_size, _exitstack)

	assert isinstance(delim, str)
	try:
		delim_alt = delim.encode(stream.encoding)
	except UnicodeEncodeError:
		pass
	else:
		assert isinstance(delim_alt, collections.abc.ByteString)
		if delim_alt:
			stream.flush()
			return map(
				fpartial(str, encoding=stream.encoding, errors=stream.errors),
				_getlines_impl_bytes(stream.buffer, delim_alt, chunk_size, _exitstack))

	#print("Using generic getlines implementation for delimiter {!r} ({!r} in {:s})".format(delim, delim_alt, stream.encoding))
	if len(delim) != 1:
	 	raise ValueError(
	 		"Delimiter must have length 1; got {!r} (length {:d})"
	 			.format(delim, len(delim)))
	return _getlines_impl_generic(stream, delim, chunk_size, _exitstack, "")


def _getlines_impl_generic(stream, delim, chunk_size, _exitstack=None,
	joiner=None
):
	assert len(delim) == 1 and chunk_size > 0
	if joiner is None:
		joiner = delim[:0]
	joiner = joiner.join
	remainder = []
	while True:
		chunk = stream.read(chunk_size)
		if not chunk:
			if chunk is None:
				raise BlockingIOError(str(stream))
			break
		chunk = chunk.split(delim)
		tail = chunk.pop()
		if chunk:
			if remainder:
				remainder.append(chunk[0])
				chunk[0] = joiner(remainder)
				remainder.clear()
			yield from chunk
		if tail:
			remainder.append(tail)
		del chunk, tail

	if remainder:
		remainder = joiner(remainder)
		yield remainder


def _getlines_impl_bytes(stream, delim, chunk_size, _exitstack):
	len_delim = len(delim)
	assert len_delim > 0 and chunk_size > 0
	if chunk_size < len_delim:
		chunk_size = len_delim + (chunk_size - len_delim % chunk_size)

	if len_delim > 1:
		def find_split_delim(remainder, buf, buf_end):
			assert len(remainder) > 0
			with remainder[ 1 - len_delim : ] as chunk1:
				with buf[ : min(len_delim - 1, buf_end) ] as chunk2:
					len_chunk1 = len(chunk1)
					pos = b"".join((chunk1, chunk2)).find(delim)

			if pos < 0:
				return (None, 0)
			assert pos < len(chunk1)
			pos -= len_chunk1
			return (remainder[:pos], pos + len_delim)

	remainder = _exitstack.enter_context(io.BytesIO())
	buf = _exitstack.enter_context(memoryview(bytearray(chunk_size)))
	while True:
		buf_end = stream.readinto(buf)
		if not buf_end:
			if buf_end is None:
				raise BlockingIOError(str(stream))
			break

		if len_delim > 1 and remainder.tell():
			# Check for delimiter split accross chunk boundaries
			remainder.truncate()
			with remainder.getbuffer() as chunk:
				chunk, chunk_start = find_split_delim(chunk, buf, buf_end)
				if chunk is not None:
					with chunk:
						yield chunk
					remainder.seek(0)
		else:
			chunk_start = 0

		while chunk_start < buf_end:
			chunk_end = buf.obj.find(delim, chunk_start, buf_end)

			if chunk_end < 0:
				with buf[chunk_start:] as chunk:
					remainder.write(chunk)
				break

			with buf[chunk_start:chunk_end] as chunk:
				if remainder.tell():
					remainder.write(chunk)
					remainder.truncate()
					with remainder.getbuffer() as chunk:
						yield chunk
					remainder.seek(0)
				else:
					yield chunk

					chunk_start = chunk_end + len_delim

	buf.release()
	if remainder.tell():
		remainder.truncate()
		yield _exitstack.enter_context(remainder.getbuffer())


if os.sep == "/":
	normpath_unix = os.path.normpath
else:
	def normpath_unix(path, *, _bytes_sep=os.fsencode(os.sep)):
		path = os.fspath(path)

		if isinstance(path, str):
			sep = os.sep
			unix_sep = "/"
		else:
			sep = _bytes_sep
			unix_sep = b"/"

		return os.path.normpath(path).replace(sep, unix_sep)


class ArgumentParser(
	argparse.ArgumentParser,
	contextlib.AbstractContextManager
):

	__slots__ = ("_exitstack",)


	def __init__(self, prog=None, *, add_help=False, description=None,
		formatter_class=argparse.ArgumentDefaultsHelpFormatter, **kwargs
	):
		if prog is None and __name__ != "__main__":
			prog = __name__
		if description is None:
			description = _(__doc__)
		kwargs["prog"] = prog
		kwargs["add_help"] = add_help
		kwargs["description"] = description
		kwargs["formatter_class"] = formatter_class
		super().__init__(**kwargs)
		self._exitstack = None

		self.add_argument("archive",
			help=_("Path to the destination archive file"))

		self.add_argument("files",
			nargs="*", help=_("A list of files to add to the archive"))

		self.add_argument("-d", "--directory", metavar="DIR",
			type=self._open_directory, default=os.curdir,
			help=_("Added file paths are relative to this directory."))

		self.add_argument("-Z", "--compression-method",
			choices=ZipFile.supported_compressors,
			default=ZipFile.supported_compressors[1],
			help=_("Select a compression method."))

		self.add_argument("--compression-level", metavar="N",
			dest="compression_level", type=self._parse_compression_level, default=-1,
			help="Set the compression level: 0 indicates no compression (store all "
				"files), lower indicates the fastest compression speed (less "
				"compression), higher indicates the slowest compression (optimal "
				"compression) and -1 indicates the default for the chosen compression "
				"method.")
		for level in range(ZipFile.compression_level_max + 1):
			self.add_argument("-" + format(level, "d"),
				action="store_const", dest="compression_level", const=level,
				help=argparse.SUPPRESS)

		self.add_argument("-y", "--symlinks",
			action="store_true",
			help=_("Add symbolic links instead of their targets to the archive."))

		default_interpreter = None
		executable_help = _(
			"Turn the archive into an executable Python ZIP application.")
		if sys.executable:
			default_interpreter = self._parse_executable(sys.executable, split=False)
			executable_help = " ".join((executable_help,
				_("If you specify an argument, its value is used as the interpreter "
					"instead of {!r}.").format(sys.executable)))
		self.add_argument("--executable", metavar="INTERPRETER",
			nargs=("?", 1)[default_interpreter is None], type=self._parse_executable,
			const=default_interpreter, help=executable_help)

		read_file_type = argparse.FileType()
		names_file_group = self.add_mutually_exclusive_group()
		names_file_group.add_argument("--names-file", metavar="FILE",
			type=read_file_type,
			help=_("Take the list of files to add from this file, one per line "
				"(after those specified on the command-line)."))
		names_file_group.add_argument("--names-file0", metavar="FILE",
			type=read_file_type,
			help=_("Like above but with NUL as line delimiter."))

		self.add_argument("-q", "--quiet",
			action="store_true",
			help=_("Don't print status notifications or the list of added files."))

		if not add_help:
			self.add_argument("-h", "--help",
				action="help", dest=argparse.SUPPRESS,
				help=_("Show this help and exit."))


	def _open_directory(self, path):
		return self.exitstack.enter_context(
			FileDescriptor(path, os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC))


	@property
	def exitstack(self):
		exitstack = self._exitstack
		if exitstack is None:
			raise RuntimeError
		return exitstack


	def __enter__(self):
		if self._exitstack is not None:
			raise RuntimeError(
				"Cannot enter an active, non-reentrant context manager")
		self._exitstack = contextlib.ExitStack().__enter__()
		return self


	def __exit__(self, exc_type, exc_value, traceback):
		exitstack = self._exitstack
		if exitstack is None:
			raise RuntimeError("Cannot exit an inactive context manager")
		self._exitstack = None
		return exitstack.__exit__(exc_type, exc_value, traceback)


	def parse_known_args(self, args, namespace):
		if self._exitstack is None:
			raise RuntimeError(
				"You must enter this argument parser's context manager before you "
					"actually use it to parse arguments.")

		r = super().parse_known_args(args, namespace)
		namespace = r[0]
		namespace.quiet = self._get_quiet_default(namespace.quiet)
		self._parse_handle_files(namespace)
		self._parse_handle_directory(namespace)
		self._parse_handle_executable(namespace)
		self._parse_handle_compression(namespace)
		self._parse_handle_archive(namespace)
		#print(namespace)
		return r


	@staticmethod
	def _parse_compression_level(s):
		max_ = ZipFile.compression_level_max
		if s == "max":
			return max_
		level = int(s)
		if not -1 <= level <= max_:
			raise ValueError(
				"Compression level must lie between -1 and {:d}, but got {:d}"
					.format(max_, level))
		return level


	def _parse_handle_files(self, ns):
		if not all(ns.files):
			self.error(_("Invalid path") + ": ''")

		if ns.names_file is not None:
			assert ns.names_file0 is None
			names_file = ns.names_file
			ns.names_file = None
			delim = names_file.newlines
			assert delim != ""
		elif ns.names_file0 is not None:
			names_file = ns.names_file0
			ns.names_file0 = None
			delim = "\0"
		else:
			names_file = None

		if names_file is not None:
			with names_file:
				ns.files.extend(filter(None, getlines(names_file, delim)))

		if not ns.files:
			self.error(_("No files to add to the archive."))


	@staticmethod
	def _parse_handle_directory(ns):
		if ns.directory is os.curdir:
			ns.directory = None


	@staticmethod
	def _parse_executable(interpreter, *, split=True, byte_limit=125):
		if ("\n" in interpreter or
			not all(c.isprintable() or c.isspace() for c in interpreter)
		):
			raise ValueError(": ".join((
				_("The interpreter string must contain only printable or whitespace characters excluding line breaks"),
				repr(interpreter))))

		interpreter_orig = interpreter
		interpreter = interpreter.split(None, 2)
		if not interpreter:
			raise ValueError(_("Empty interpreter"))
		if len(interpreter) > bool(split) + 1:
			raise ValueError(": ".join((
				_("Surplus whitespace in interpreter string"), repr(interpreter_orig))))

		exe = interpreter[0]
		if os.path.basename(exe) in ("", os.curdir, os.pardir):
			raise ValueError(": ".join((
				_("The interpreter executable path refers to a directory"), repr(exe))))
		if not os.path.isabs(exe) or os.path.splitdrive(exe)[0]:
			raise ValueError(": ".join((
				_("The interpreter executable path must be absolute and free of drive "
					"or UNC host prefixes"),
				repr(exe))))

		interpreter[0] = exe = normpath_unix(exe)
		interpreter = os.fsencode(" ".join(interpreter))

		if len(interpreter) > byte_limit:
			raise ValueError(": ".join((
				_("The normalized and encoded interpreter line exceeds {:n} bytes")
					.format(byte_limit),
				repr(interpreter))))

		return interpreter


	def _parse_handle_executable(self, ns):
		if ns.executable is NotImplemented:
			refname = "sys.executable"
			self.error(
				_("Unable to determine a default interpreter from the runtime "
					"environment ({:s}={!r}). Please specify it explicitly.")
						.format(refname, eval(refname)))


	@staticmethod
	def _parse_handle_compression(ns):
		ns.compression_method = ZipFile.compressor_ids[ ns.compression_method ]


	@staticmethod
	def _get_quiet_default(value=False):
		if value or sys.stdout is None or sys.stdout.closed:
			return True

		stdout_fileno = getattr(sys.stdout, "fileno", None)
		if stdout_fileno is not None:
			stdout_fileno = stdout_fileno()
			if stdout_fileno is not None:
				try:
					return is_dev_null(stdout_fileno)
				except OSError as ex:
					e = errno
					if ex.errno not in { e.EACCES, e.EBADF, e.ENOENT, e.ENOTDIR }:
						raise
					if __debug__:
						traceback.print_exc()

		return False


	def _parse_handle_archive(self, ns):
		f_archive = self.exitstack.enter_context(
			open(ns.archive, "wb",
				opener=fpartial(os.open, mode=0o777 if ns.executable else 0o666)))
		ns.archive = self.exitstack.enter_context(
			ZipFile(f_archive, "w", ns.compression_method,
				compress_options=ns.compression_level))


def is_dev_null(file, *,
	null_device_paths=(b"/dev/null", b"/dev/zero"),
	null_device_numbers=set() if hasattr(os.stat_result, "st_rdev") else None
):
	assert null_device_paths
	f_stat = os.stat(file)

	if null_device_numbers is not None:
		if not f_stat.st_rdev:
			return False
		if not null_device_numbers:
			null_device_numbers.update(
				map(operator.attrgetter("st_rdev"), map(os.stat, null_device_paths)))
		if null_device_numbers:
			return f_stat.st_rdev in null_device_numbers
		is_dev_null.__kwdefaults__["null_device_numbers"] = None

	return (
		stat.S_ISCHR(f_stat.st_mode) and
		any(map(
			fpartial(os.path.samestat, f_stat), map(os.stat, null_device_paths))))


def format_size(num, unit="B", num_fmt=None,
	fmt="{:{:s}} {:{:d}s}{:s}".format,
	magnitudes=tuple(itertools.accumulate(
		(("", 0), "K", "M", "G", "T", "P", "E", "Z", "Y"),
		lambda acc, c: (c, (acc[1] or 1) * 1000))),
	*, floor_division=False
):
	if not callable(fmt):
		fmt = fmt.format

	floor_division = bool(floor_division)
	if num_fmt is None:
		num_fmt = ("4.3n", "4n")[floor_division]
	elif isinstance(num_fmt, int):
		num_fmt = max(num_fmt, 1)
		num_fmt = (
			("{:d}.{:d}n", "{:d}n")[floor_division].format(num_fmt, num_fmt - 1))

	abs_num = abs(num)
	magnitudes = iter(magnitudes)
	prefix, magnitude = next(magnitudes, ("", 0))
	magnitude = 0
	len_prefix = len(prefix)
	for next_prefix, next_magnitude in magnitudes:
		len_prefix = max(len_prefix, len(next_prefix))
		if abs_num < next_magnitude:
			len_prefix = max(
				len_prefix, max(map(len, map(itemgetter0, magnitudes)), default=0))
			break
		prefix = next_prefix
		magnitude = next_magnitude

	if not magnitude:
		magnitude = 1

	if floor_division:
		num //= magnitude
	else:
		num /= magnitude

	return fmt(num, num_fmt, prefix, len_prefix, unit)


def main(args=None):
	with ArgumentParser() as ap:
		args = ap.parse_args(args)
		quiet = args.quiet
		archive = args.archive
		directory = args.directory
		follow_symlinks = not args.symlinks

		if args.executable:
			shebang = args.executable.join((b"#!", b"\n"))
			archive.fp.write(shebang)
			archive.start_dir += len(shebang)
			del shebang

		if not quiet:
			print(
				_("Compressing files into {:s}").format(archive.fp.name),
				end=":\n\n")

		fail_count = 0
		for file in args.files:
			try:
				info = archive.write(
					file, dir_fd=directory, follow_symlinks=follow_symlinks)
			except EnvironmentError as ex:
				print(ex, file=sys.stderr)
				fail_count += 1
			else:
				if not quiet:
					print(
						"{:s} => {:s} ({:4.0%})".format(
							format_size(info.file_size), format_size(info.compress_size),
							info.file_size and info.compress_size / info.file_size),
						file, sep="  ")

		main_py = "__main__.py"
		if args.executable and main_py not in archive.NameToInfo:
			print(
				_("Warning: Executable Python ZIP archives require a file {!r} in the "
					"archive root directory to work but you omitted it.")
						.format(main_py),
				file=sys.stderr)

	if not fail_count:
		print("", _("Everything is OK."), sep="\n")
	return int(bool(fail_count))


if __name__ == "__main__":
	import locale
	locale.setlocale(locale.LC_ALL, "")
	sys.exit(main())
