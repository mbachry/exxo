import os
import sys
import stat
import inspect
import ctypes
import subprocess
import pytest


BUNDLED_FILE = os.path.join(os.path.dirname(__file__), 'pkg', 'files', 'foo')


def test_bundled_file_open():
    with open(BUNDLED_FILE, 'rb') as fp:
        buf = fp.read().strip()
    assert buf == b'foo'
    with open(BUNDLED_FILE) as fp:
        buf2 = fp.read().strip()
    assert buf2 == 'foo'


def test_bundled_file_open_not_writable():
    with pytest.raises(OSError):
        with open(BUNDLED_FILE, 'w') as fp:
            fp.write('bar')


def test_bundled_file_stat():
    st = os.stat(BUNDLED_FILE)
    assert st.st_size == 4
    assert stat.S_ISREG(st.st_mode)
    assert int(st.st_mtime) == int(os.stat(sys.executable).st_mtime)
    assert os.path.exists(BUNDLED_FILE)
    assert os.path.isfile(BUNDLED_FILE)


def test_bundled_dir_stat():
    d = os.path.dirname(BUNDLED_FILE)
    st = os.stat(d)
    assert stat.S_ISDIR(st.st_mode)
    assert int(st.st_mtime) == int(os.stat(sys.executable).st_mtime)
    assert os.path.exists(d)
    assert os.path.isdir(d)


def test_bundled_dir_list():
    d = os.path.dirname(BUNDLED_FILE)
    files = os.listdir(d)
    assert files == ['foo']


def test_inspect_bundled_source():
    from inzip.pkg import some
    s = inspect.getsourcefile(some)
    assert s.endswith('.py')


def test_ctypes_dlopen_from_bundled_lib():
    libfile = os.path.join(os.path.dirname(__file__), 'spamtypes.so')
    lib = ctypes.CDLL(libfile)
    lib.add.argtypes = [ctypes.c_int, ctypes.c_int]
    lib.add.restype = ctypes.c_int
    res = lib.add(7, 9)
    assert res == 16


def test_subprocess_from_bundled_exe():
    exe = os.path.join(os.path.dirname(__file__), 'spam')
    subprocess.check_call([exe])


@pytest.mark.xfail(reason='broken for now')
def test_subprocess_output_from_bundled_exe():
    exe = os.path.join(os.path.dirname(__file__), 'spam')
    buf = subprocess.check_output([exe]).decode().strip()
    assert buf == 'hello'


def test_subprocess_with_cwd_inside_zip():
    d = os.path.join(os.path.dirname(__file__))
    exe = os.path.join(d, 'spam')
    subprocess.check_call([exe], cwd=d)


def test_subprocess_can_launch_itself_as_python_interpreter():
    buf = subprocess.check_output([sys.executable, '-V']).decode().strip()
    assert buf.startswith('pyrun')
