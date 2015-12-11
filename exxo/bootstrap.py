import sys
import subprocess
import shutil
import tarfile
import pkgutil
import argparse
from pathlib import Path
from urllib.request import urlopen


PYTHON_VERSION_MAP = {
    '3.4': {
        'full_version': '3.4.3',
        'patch': Path('patches/python34.diff'),
        'unicode': 'ucs4',
    },
    '2.7': {
        'full_version': '2.7.11',
        'patch': Path('patches/python27.diff'),
        'unicode': 'ucs2',
    },
}

PYRUN_VERSION = '2.1.1'
SETUPTOOLS_VERSION = '18.4'
PIP_VERSION = '7.1.2'
PYRUN_SRC_URL = 'https://downloads.egenix.com/python/egenix-pyrun-{}.tar.gz'.format(PYRUN_VERSION)
PYRUN_SRC_DIR = 'egenix-pyrun-{}'.format(PYRUN_VERSION)
SETUPTOOLS_URL = 'https://pypi.python.org/packages/source/s/setuptools/setuptools-{}.tar.gz'.format(SETUPTOOLS_VERSION)
PIP_URL = 'https://pypi.python.org/packages/source/p/pip/pip-{}.tar.gz'.format(PIP_VERSION)
BUILD_DIR = 'build'


def ensure_dir_exists(d):
    d.mkdir(parents=True, exist_ok=True)


def download_url(url, dst_file):
    with urlopen(url) as src, dst_file.open('wb') as dst:
        shutil.copyfileobj(src, dst)


def download_and_unpack(url, dst_path, dst_dir):
    print('downloading', url)
    download_url(url, dst_path)
    try:
        print('unpacking', dst_path)
        with tarfile.open(str(dst_path)) as tar:
            tar.extractall(str(dst_dir))
    finally:
        dst_path.unlink()


def patch(dst_path, diff):
    cmd = ['patch', '-p1']
    proc = subprocess.Popen(cmd, cwd=str(dst_path), stdin=subprocess.PIPE)
    proc.communicate(diff)
    if proc.returncode != 0:
        raise RuntimeError('command {} failed with return code: {}'
                           .format(cmd, proc.returncode))


class Bootstrap:
    def __init__(self, python_version):
        self.python_major_version = python_version
        self.meta = PYTHON_VERSION_MAP[python_version]
        self.python_full_version = self.meta['full_version']
        builddir = Path(BUILD_DIR)
        ensure_dir_exists(builddir)
        self.builddir = builddir.resolve()
        self.targetdir = self.builddir / 'target-{}'.format(self.python_major_version)
        self.pyrun_dir = self.builddir / PYRUN_SRC_DIR / 'PyRun'
        self.pyrun = self.targetdir / 'bin' / 'pyrun{}'.format(self.python_major_version)

    def pyrun_make(self, target):
        # pyrun seems to compile incorrectly, if compiled with -jN
        # larger than 1
        subprocess.check_call(['make', '-j1', target, 'PYTHONFULLVERSION=' + self.python_full_version],
                              cwd=str(self.pyrun_dir))

    def install_setuptools(self):
        download_and_unpack(SETUPTOOLS_URL, self.builddir / 'setuptools.tar.gz', self.builddir)
        setup_py = self.builddir / 'setuptools-{}'.format(SETUPTOOLS_VERSION) / 'setup.py'
        subprocess.check_call([str(self.pyrun), str(setup_py), 'install'])

    def install_pip(self):
        download_and_unpack(PIP_URL, self.builddir / 'pip.tar.gz', self.builddir)
        pip_src_dir = self.builddir / 'pip-{}'.format(PIP_VERSION)
        setup_py = pip_src_dir / 'setup.py'
        subprocess.check_call([str(self.pyrun), str(setup_py), 'install'], cwd=str(pip_src_dir))

    def install_pyrun(self):
        # download, unpack and patch pyrun
        pyrun_src_tar = self.builddir / 'pyrun.tar.gz'
        download_and_unpack(PYRUN_SRC_URL, pyrun_src_tar, self.builddir)
        pyrun_diff = pkgutil.get_data(__package__, 'patches/pyrun.diff')
        patch(self.builddir / PYRUN_SRC_DIR, pyrun_diff)
        # giving full python source path as makefile target makes pyrun
        # download and patch python
        python_dir = self.pyrun_dir / 'Python-{}-{}'.format(self.python_full_version,
                                                              self.meta['unicode'])
        self.pyrun_make(str(python_dir))
        # apply our python patches too
        py_patch_path = PYTHON_VERSION_MAP[self.python_major_version]['patch']
        python_diff = pkgutil.get_data(__package__, str(py_patch_path))
        patch(python_dir, python_diff)
        # configure ffi (for ctypes)
        ffi_config_script = python_dir / 'Modules' / '_ctypes' / 'libffi' / 'configure'
        ffi_build_dir = (python_dir / 'build' /
                         'temp.linux-x86_64-{}'.format(self.python_major_version) /
                         'libffi')
        ensure_dir_exists(ffi_build_dir)
        subprocess.check_call([str(ffi_config_script)], cwd=str(ffi_build_dir))
        # build pyrun and move it to top build directory
        self.pyrun_make('pyrun')
        pyrun_target_dir = self.pyrun_dir / 'build-{}-{}'.format(self.python_major_version,
                                                                 self.meta['unicode'])
        pyrun_bin = (pyrun_target_dir / 'bin' / self.pyrun.name)
        ensure_dir_exists(self.targetdir / 'bin')
        ensure_dir_exists(self.targetdir / 'lib' /
                          'python{}'.format(self.python_major_version) /
                          'site-packages')
        pyrun_bin.rename(self.pyrun)
        (pyrun_target_dir / 'include').rename(self.targetdir / 'include')

    def bootstrap(self):
        self.install_pyrun()
        self.install_setuptools()
        self.install_pip()


def main():
    parser = argparse.ArgumentParser(description='exxo bootstrap', prog='exxo')
    parser.add_argument('major_version', nargs='+',
                        help='python major version to bootstrap (or "all")')
    args = parser.parse_args()
    versions = args.major_version
    if 'all' in versions:
        versions = PYTHON_VERSION_MAP.keys()
    for version in versions:
        if version not in PYTHON_VERSION_MAP:
            sys.exit('unsupported python version: {}'.format(version))
    for version in versions:
        b = Bootstrap(version)
        b.bootstrap()


if __name__ == '__main__':
    main()
