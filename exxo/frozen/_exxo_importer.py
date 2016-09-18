import sys
import os
import zipfile
import sysconfig
import shutil
import tempfile
import imp
import warnings


class ModuleImporter(object):
    def __init__(self):
        if not zipfile.is_zipfile(sys.executable):
            self.exe_zip = None
            return
        self.exe_zip = zipfile.ZipFile(sys.executable, 'r')
        self.exe_names = self.exe_zip.namelist()
        self.ext_suffix = sysconfig.get_config_var('SO')

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
        tmpdir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmpdir, so_file)
        try:
            self._extract_so_file(path, tmp_path)
            self._handle_rpath(path, tmp_path)
            if sys.version_info[0] == 2:
                name = fullname.split('.')[-1]
                mod = imp.load_dynamic(name, tmp_path)
            else:
                from importlib.machinery import ExtensionFileLoader
                loader = ExtensionFileLoader(fullname, tmp_path)
                spec.origin = tmp_path
                mod = loader.create_module(spec)
            sys.modules[fullname] = mod
            return mod
        finally:
            try:
                shutil.rmtree(tmpdir)
            except OSError:
                pass

    def _extract_so_file(self, src, dst):
        with self.exe_zip.open(src) as src:
            with open(dst, 'wb') as dst:
                shutil.copyfileobj(src, dst)
                os.fchmod(dst.fileno(), 0o700)

    def _get_path_in_zip(self, fullname):
        path = '{}{}'.format(fullname.replace('.', '/'), self.ext_suffix)
        return path if path in self.exe_names else None

    def _handle_rpath(self, zip_path, solib_path, cur_rpath=None):
        print('@@@@', zip_path, solib_path, cur_rpath)
        print('@@ platform', sys.platform)
        if sys.platform not in ('linux', 'linux2'):
            return
        try:
            import _exxo_elf
        except ImportError:
            # for unit tests
            from . import _exxo_elf
        dst_dir = os.path.dirname(solib_path)
        elf = _exxo_elf.readelf(solib_path)
        dyntab = elf['dynamic']
        rpath = dyntab.get(_exxo_elf.DT_RPATH, [])
        print('@@ rpath', rpath)
        if not rpath:
            if cur_rpath is None:
                return
            # if RPATH was specified as a param, we go with this one,
            # even if given solib has no RPATH section - this allows
            # handling dependecies recursively
            rpath = cur_rpath
        else:
            rpath = rpath[0].decode()
            # replace current RPATH with $ORIGIN and copy referenced
            # libraries to the same directory as extension module solib
            new_rpath = '$ORIGIN'
            # TODO: if RPATH is shorter than $ORIGIN all we do is hope
            # RPATH is not needed at all
            if len(rpath) < len(new_rpath):
                warnings.warn("can't overwrite RPATH {} with {}".format(rpath, new_rpath))
                return
            with open(solib_path, 'rb+') as fp:
                fp.seek(elf['rpath_offset'], os.SEEK_SET)
                fp.write(new_rpath.encode() + b'\0')
            print('@@ new_rpath', new_rpath)
        # extract dependencies from zip, if any. put them in the same
        # temporary directory
        origin = os.path.dirname(zip_path)
        rpath = os.path.normpath(rpath.replace('$ORIGIN', origin))
        for lib in dyntab.get(_exxo_elf.DT_NEEDED, []):
            lib = lib.decode()
            path = os.path.normpath('{}/{}'.format(rpath, lib))
            print('@@ normpath', path)
            if path in self.exe_names:
                dst = os.path.join(dst_dir, lib)
                self._extract_so_file(path, dst)
                print('@@ extract', path, dst)
                # extract dependecies recursively
                self._handle_rpath(path, dst, cur_rpath=rpath)


exxo_importer = ModuleImporter()
