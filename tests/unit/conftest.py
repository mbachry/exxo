import sys
import os
import subprocess
import zipapp
import shutil
import tempfile
import sysconfig
from unittest import mock
from pathlib import Path
import pytest

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(base_dir))

from exxo.frozen._exxo_importer import ModuleImporter


def test_zipimport_hook(testdir, tmpdir):
    """Test package loader is being used correctly (see #1837)."""
    testdir.tmpdir.join('app').ensure(dir=1)
    testdir.makepyfile(**{
        'app/foo.py': """
            import pytest
            def main():
                pytest.main(['--pyarg', 'foo'])
        """,
    })
    target = tmpdir.join('foo.zip')
    zipapp.create_archive(str(testdir.tmpdir.join('app')), str(target), main='foo:main')
    result = testdir.runpython(target)
    assert result.ret == 0
    result.stderr.fnmatch_lines(['*not found*foo*'])
    assert 'INTERNALERROR>' not in result.stdout.str()


def _create_init_py(path):
    with (path / '__init__.py').open('w'):
        pass


@pytest.yield_fixture(scope='session')
def zip_app():
    testdir = base_dir / 'tests'
    subprocess.check_call(['python3', 'setup.py', 'build_ext', '--inplace'],
                          cwd=str(testdir / 'inzip'))
    subprocess.check_call(['python3', 'setup.py', 'build_ext', '--inplace'],
                          cwd=str(testdir / 'testapp'))
    tmpdir = tempfile.mkdtemp()
    sofile = 'spam{}'.format(sysconfig.get_config_var('SO'))
    rpath_sofile = 'rpath{}'.format(sysconfig.get_config_var('SO'))
    shutil.copy(str(testdir / 'inzip' / 'inzip' / 'pkg' / sofile), tmpdir)
    # arrange rpath extension so its solib dependency sits in a
    # directory below it (as defined in RPATH)
    subdir = Path(tmpdir) / 'sub' / 'sub2'
    subdir.mkdir(parents=True)
    _create_init_py(Path(tmpdir) / 'sub')
    _create_init_py(subdir)
    shutil.copy(str(testdir / 'testapp' / rpath_sofile), str(subdir))
    shutil.copy(str(testdir / 'inzip' / 'inzip' / 'spamtypes.so'),
                str(Path(tmpdir) / 'sub' / 'libspamtypes.so'))
    with (Path(tmpdir) / 'foo.py').open('w') as fp:
        fp.write("""
        def main():
            pass
        """)
    _, app = tempfile.mkstemp('.zip')
    zipapp.create_archive(str(tmpdir), app, main='foo:main')
    yield app
    shutil.rmtree(tmpdir)
    os.unlink(app)


@pytest.yield_fixture
def importer(zip_app):
    with mock.patch.object(sys, 'executable', zip_app):
        importer = ModuleImporter()
        meta = sys.meta_path + [importer]
        path = sys.path + [zip_app]
        with mock.patch.object(sys, 'meta_path', meta):
            with mock.patch.object(sys, 'path', path):
                yield importer
    sys.modules.pop('spam', None)
    sys.modules.pop('sub.sub2.rpath', None)
