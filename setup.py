#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='exxo',
    version='0.0.1',
    description="Python Boilerplate contains all the boilerplate you need to create a Python package.",
    long_description=readme,
    author="Marcin Bachry",
    author_email='hegel666@gmail.com',
    url='https://github.com/mbachry/exxo',
    packages=[
        'exxo',
    ],
    package_dir={'exxo':
                 'exxo'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=True,
    keywords='exxo',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
