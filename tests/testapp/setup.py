import subprocess
from setuptools import setup, Extension
from pathlib import Path


testdir = Path(__file__).resolve().parent.parent
inzip_dir = testdir / 'inzip' / 'inzip'
if not (inzip_dir / 'spamtypes.so').exists():
    subprocess.check_call(['make', '-C', str(testdir / 'inzip'), 'inzip/spamtypes.so'])
symlink = (inzip_dir / 'libspamtypes.so')
if not symlink.exists():
    symlink.symlink_to(inzip_dir / 'spamtypes.so')


ext = Extension(
    'rpath',
    sources=['rpath.c'],
    library_dirs=[str(inzip_dir)],
    libraries=['spamtypes'],
    extra_link_args=['-Wl,-rpath,/some/path:$ORIGIN/..']
)


setup(
    name='rpath',
    version='0.0.1',
    description="test rpath extension",
    ext_modules=[ext]
)
