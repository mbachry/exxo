def test_find_solib_in_zip(importer):
    spec = importer.find_spec('spam', None)
    assert spec is not None


def test_find_solib_in_zip_missing(importer):
    spec = importer.find_spec('spam_missing', None)
    assert spec is None


def test_import_solib_from_zip(importer):
    import spam
    assert spam.spam(2, 6) == 8


def test_import_rpath_solib_from_zip(importer):
    from sub.sub2 import rpath
    assert rpath.spam(2, 6) == 8
