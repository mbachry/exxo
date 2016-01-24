import sys


def test_import_solib():
    from inzip.pkg import spam
    res = spam.spam(5, 7)
    assert res == 12
    # solibs are unpacked to /tmp in current implementation
    assert spam.__file__.startswith('/tmp/zipimport')


def test_imports_module_from_pyc():
    from inzip.pkg import some
    assert some.__file__.endswith('.pyc')
    assert some.__file__.startswith(sys.executable)


def test_imports_package_from_pyc():
    from inzip import pkg
    assert pkg.__file__.endswith('.pyc')
    assert pkg.__file__.startswith(sys.executable)
