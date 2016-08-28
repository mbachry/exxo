import os
import sys
import argparse
import subprocess
import shutil
import configparser
import pkgutil
import tarfile
import tempfile
import zipfile
import io
import zipapp
from pathlib import Path
import jinja2
from .bootstrap import PYTHON_VERSION_MAP, ensure_dir_exists
from .venv import ACTIVATE_SCRIPT, PIP_SCRIPT


def create_binary(dst_path, pyrun, zip_file, compress_pyrun):
    if compress_pyrun:
        pyrun_upx = pyrun.with_name(pyrun.name + '.compressed')
        if not pyrun_upx.exists():
            pyrun_upx_tmp = pyrun_upx.with_name(pyrun_upx.name + '.tmp')
            shutil.copy(str(pyrun), str(pyrun_upx_tmp))
            try:
                subprocess.check_call(['upx', str(pyrun_upx_tmp)])
            except FileNotFoundError:
                sys.exit('error: compression is enabled, but upx command was not found')
            pyrun_upx_tmp.rename(pyrun_upx)
        pyrun = pyrun_upx
    basedir = dst_path.parent
    if basedir:
        ensure_dir_exists(basedir)
    with dst_path.open('wb') as dst_fp, pyrun.open('rb') as pyrun_fp, zip_file.open('rb') as zip_fp:
        shutil.copyfileobj(pyrun_fp, dst_fp)
        shutil.copyfileobj(zip_fp, dst_fp)
    dst_path.chmod(0o0755)


def create_virtualenv(args):
    builddir = Path('pyrun') / args.py_version
    envdir = Path(args.envdir)
    bindir = envdir / 'bin'
    libdir = envdir / 'lib' / 'python{}'.format(args.py_version) / 'site-packages'
    pipdir = envdir / 'pip'
    for d in (bindir, libdir, pipdir):
        ensure_dir_exists(d)
    # setup bin dir
    pyrun = bindir / 'pyrun{}'.format(args.py_version)
    with pyrun.open('wb') as fp:
        fp.write(pkgutil.get_data(__package__, str(builddir / 'pyrun')))
    pyrun.chmod(0o755)
    (bindir / 'python').symlink_to(pyrun.name)
    (bindir / 'python{}'.format(args.py_version[0])).symlink_to(pyrun.name)
    (bindir / 'python{}'.format(args.py_version)).symlink_to(pyrun.name)
    tmpl = jinja2.Template(ACTIVATE_SCRIPT)
    with (bindir / 'activate').open('w') as fp:
        fp.write(tmpl.render(
            venv_path=str(envdir.resolve()),
            venv_name=envdir.name,
            pyrun_version=args.py_version))
    # setup include dir
    include_tar = io.BytesIO(pkgutil.get_data(__package__, str(builddir / 'include.tar')))
    with tarfile.open(fileobj=include_tar) as tar:
        tar.extractall(str(envdir))
    # install setuptools & pip
    for fn in ('setuptools.whl', 'pip.whl'):
        data = pkgutil.get_data(__package__, str(builddir / fn))
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(str(pipdir))
    pip_bin = bindir / 'pip'
    with (pip_bin).open('w') as fp:
        fp.write(PIP_SCRIPT)
    pip_bin.chmod(0o755)


def get_project_name(source_path):
    out = subprocess.check_output(['python', 'setup.py', '--name'], cwd=source_path)
    lines = out.decode().splitlines()
    if not lines:
        sys.exit('failed to get project name from setup.py (python setup.py --name): empty output')
    return lines[-1]


def get_entry_point(source_path, project_name=None):
    project_name = project_name or get_project_name(source_path)
    conf = configparser.ConfigParser()
    with tempfile.TemporaryDirectory() as tempdir:
        subprocess.check_call(['python', 'setup.py', 'egg_info',
                               '--egg-base={}'.format(tempdir)],
                              cwd=source_path)
        meta_file = Path(tempdir) / '{}.egg-info'.format(project_name) / 'entry_points.txt'
        conf.read(str(meta_file))
    if not conf.has_section('console_scripts'):
        sys.exit('no "console_scripts" entry point in setup.py. either provide it or '
                 'use --main parameter')
    keys = conf.options('console_scripts')
    if len(keys) != 1:
        # TODO; fix it
        sys.exit('only one console script can be used for now')
    return conf.get('console_scripts', keys[0])


def build(args):
    envdir = os.environ.get('VIRTUAL_ENV')
    if envdir is None:
        sys.exit('virtualenv not activated')
    envdir = Path(envdir)
    py_version = os.environ.get('VIRTUAL_ENV_PYRUN_VERSION')
    if py_version is None:
        sys.exit('current virtualenv is not an exxo virtualenv')
    pyrun = envdir / 'bin' / 'pyrun{}'.format(py_version)
    site_packages = envdir / 'lib' / 'python{}'.format(py_version) / 'site-packages'
    zip_file = envdir / 'app.zip'
    # make sure pip undestands it as a local directory
    source_path = args.source_path.rstrip(os.sep) + os.sep
    project_name = get_project_name(source_path)
    entry_point = args.main or get_entry_point(source_path, project_name)
    subprocess.check_call(['pip', 'install', '-U', source_path])
    dst_bin = Path(args.output or (Path(source_path) / 'dist' / project_name))
    zipapp.create_archive(site_packages, zip_file, main=entry_point)
    create_binary(dst_bin, pyrun, zip_file, args.compress_pyrun)


def main():
    py_versions = list(PYTHON_VERSION_MAP.keys())
    parser = argparse.ArgumentParser(description='exxo builder', prog='exxo')
    subparsers = parser.add_subparsers(title='subcommands', description='valid commands', dest='cmd')
    subparsers.required = True
    parser_venv = subparsers.add_parser('venv', help='create virtualenv')
    parser_venv.add_argument('envdir', help='virtualenv directory')
    parser_venv.add_argument('-p', '--py-version', choices=py_versions, default='3.5',
                             help='python version to use (default: 3.5)')
    parser_venv.set_defaults(func=create_virtualenv)
    parser_build = subparsers.add_parser('build', help='build')
    parser_build.add_argument('-o', '--output', help='target binary')
    parser_build.add_argument('--main', help='main function: package.module:function')
    parser_build.add_argument('-s', '--source-path', default='.', help='path to project source')
    parser_build.add_argument('-c', '--compress-pyrun', action='store_true',
                              help='compress pyrun binary with upx')
    parser_build.set_defaults(func=build)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
