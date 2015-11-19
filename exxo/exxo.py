import os
import argparse
import subprocess
import zipapp
import tempfile
import struct
import shutil
from pathlib import Path


def create_binary(dst_path, pyrun, zip_file):
    packer = struct.Struct('IQ')
    pos = pyrun.stat().st_size
    # make_t()
    with dst_path.open('wb') as dst_fp, pyrun.open('rb') as pyrun_fp, zip_file.open('rb') as zip_fp:
        shutil.copyfileobj(pyrun_fp, dst_fp)
        shutil.copyfileobj(zip_fp, dst_fp)
        meta = packer.pack(0xdeadbeef, pos)
        dst_fp.write(meta)
    dst_path.chmod(0o0755)


def main():
    parser = argparse.ArgumentParser(description='exxo builder', prog='exxo')
    parser.add_argument('-r', '--requirement', action='append', default=[], help='pip package name')
    parser.add_argument('source_path', help='source package directory')
    parser.add_argument('main', help='main function: package.module:function')
    parser.add_argument('dest_bin', help='target binary')
    args = parser.parse_args()
    builddir = Path('build')
    pip = str(builddir / 'bin' / 'pip')
    pyrun = builddir / 'bin' / 'pyrun3.4'  # TODO: fixed py version
    # install_path = tempfile.mkdtemp()

    install_path = builddir / 'install'
    pip_root = install_path / 'pip_root'
    pip_root.mkdir(parents=True, exist_ok=True)
    zip_file = install_path / 'app.zip'

    try:
        cmd = [pip, 'install', '--target', str(pip_root)]
        if args.requirement:
            subprocess.check_call(cmd + args.requirement)
        # make sure pip undestands it as a local directory
        source_path = args.source_path.rstrip(os.sep) + os.sep
        subprocess.check_call(cmd + [source_path])
        zipapp.create_archive(pip_root, zip_file, main=args.main)
        create_binary(Path(args.dest_bin), pyrun, zip_file)
    finally:
        # shutil.rmtree(install_path)
        pass


if __name__ == '__main__':
    main()
