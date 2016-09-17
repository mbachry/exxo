import sys
import os
import posix
import stat
import zipfile
import errno
from _exxo_importer import exxo_importer


zip_cache = {}


def cached(func):
    cache = zip_cache.setdefault(func, {})
    def wrapped(*args):
        ent = cache.get(args)
        if ent is None:
            ent = func(*args)
            cache[args] = ent
        return ent
    return wrapped


@cached
def _get_inzip_path(filename, exc):
    if not zipfile.is_zipfile(sys.executable):
        raise exc(errno.ENOENT, filename)
    inzip_path = filename[len(sys.executable):].lstrip('/')
    if inzip_path not in exxo_importer.exe_names:
        # try a directory
        inzip_path = inzip_path + '/'
        if inzip_path not in exxo_importer.exe_names:
            raise exc(errno.ENOENT, filename)
    is_dir = inzip_path.endswith('/')
    return inzip_path, is_dir


def get_file(filename):
    inzip_path, _ = _get_inzip_path(filename, IOError)
    return exxo_importer.exe_zip.open(inzip_path)


@cached
def stat_file(filename):
    inzip_path, is_dir = _get_inzip_path(filename, OSError)
    info = exxo_importer.exe_zip.getinfo(inzip_path)
    stat_result = list(os.stat(sys.executable))
    stat_result[6] = info.file_size
    if is_dir:
        stat_result[0] &= ~(stat.S_IFREG | stat.S_IFLNK)
        stat_result[0] |= stat.S_IFDIR
    return posix.stat_result(stat_result)


@cached
def listdir(directory):
    fixed_directory = directory.rstrip('/') + '/'
    inzip_path, is_dir = _get_inzip_path(fixed_directory, OSError)
    if not is_dir:
        raise OSError(errno.ENOTDIR, directory)
    return [n[len(inzip_path):] for n in exxo_importer.exe_names
            if n != inzip_path and n.startswith(inzip_path)]
