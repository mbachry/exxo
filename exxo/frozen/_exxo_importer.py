import sys
import os
import zipfile
import sysconfig
import shutil
import tempfile
import imp


class ModuleImporter(object):
    def __init__(self):
        if not zipfile.is_zipfile(sys.executable):
            self.exe_zip = None
            return
        self.exe_zip = zipfile.ZipFile(sys.executable, 'r')
        self.exe_names = self.exe_zip.namelist()
        self.ext_suffix = sysconfig.get_config_var('SO')
        self.tmpdir = tempfile.gettempdir()

    def find_spec(self, fullname, path, target=None):
        if self.exe_zip is None:
            return
        from importlib.machinery import ModuleSpec
        path = self._get_path_in_zip(fullname)
        if path is not None:
            return ModuleSpec(fullname, self, origin=path)

    def find_module(self, fullname, path=None):
        if self.exe_zip is None:
            return
        path = self._get_path_in_zip(fullname)
        return self if path else None

    def load_module(self, fullname):
        if self.exe_zip is None:
            return
        if fullname in sys.modules:
            return sys.modules[fullname]
        if sys.version_info[0] == 3:
            spec = self.find_spec(fullname, None)
            assert spec is not None
            path = spec.origin
        else:
            path = self._get_path_in_zip(fullname)
        assert path is not None
        so_file = os.path.basename(path)
        tmp_path = os.path.join(self.tmpdir, so_file)
        tmp_files = [tmp_path]
        try:
            self._extract_so_file(path, tmp_path)
            if sys.version_info[0] == 2:
                name = fullname.split('.')[-1]
                mod = imp.load_dynamic(name, tmp_path)
            else:
                from importlib.machinery import ExtensionFileLoader
                loader = ExtensionFileLoader(fullname, tmp_path)
                spec.origin = tmp_path
                mod = loader.create_module(spec)
            return mod
        finally:
            self._delete_tmp_files(tmp_files)

    def _extract_so_file(self, src, dst):
        with self.exe_zip.open(src) as src:
            with open(dst, 'wb') as dst:
                shutil.copyfileobj(src, dst)
                os.fchmod(dst.fileno(), 0o700)

    def _get_path_in_zip(self, fullname):
        path = '{}{}'.format(fullname.replace('.', '/'), self.ext_suffix)
        return path if path in self.exe_names else None

    def _delete_tmp_files(self, files):
        for path in files:
            try:
                os.unlink(path)
            except OSError:
                pass


exxo_importer = ModuleImporter()
