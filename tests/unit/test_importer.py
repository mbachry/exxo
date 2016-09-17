def test_find_solib_in_zip(importer):
    spec = importer.find_spec('spam', None)
    assert spec is not None


def test_find_solib_in_zip_missing(importer):
    spec = importer.find_spec('spam_missing', None)
    assert spec is None


def test_import_solib_from_zip(importer):
    mod = importer.load_module('spam')
    assert mod is not None
    func = getattr(mod, 'spam')
    assert func(2, 6) == 8
