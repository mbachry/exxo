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


@pytest.yield_fixture(scope='session')
def zip_app():
    inzip_dir = base_dir / 'tests' / 'inzip'
    subprocess.check_call(['python', 'setup.py', 'build_ext', '--inplace'], cwd=str(inzip_dir))
    tmpdir = tempfile.mkdtemp()
    sofile = 'spam{}'.format(sysconfig.get_config_var('SO'))
    shutil.copy(str(inzip_dir / 'inzip' / 'pkg' / sofile), tmpdir)
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
        yield importer
    sys.modules.pop('spam', None)
