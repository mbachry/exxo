#!/usr/bin/env python3
from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    'jinja2',
]

test_requirements = [
    'pytest',
]

setup(
    name='exxo',
    version='0.0.5',
    description="Build portable Python apps",
    long_description=readme,
    author="Marcin Bachry",
    author_email='hegel666@gmail.com',
    url='https://github.com/mbachry/exxo',
    packages=['exxo'],
    package_dir={'exxo': 'exxo'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'exxo = exxo.exxo:main',
        ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ]
)
