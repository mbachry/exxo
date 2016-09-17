from setuptools import setup, Extension

requirements = [
    'pytest',
    'setuptools',
    'requests',
    'numpy',
]

ext = Extension('inzip.pkg.spam', sources=['inzip/pkg/spam.c'])

setup(
    name='inzip',
    version='0.0.1',
    description="run tests inside built binary",
    packages=['inzip'],
    ext_modules=[ext],
    include_package_data=True,
    install_requires=requirements,
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'inzip = pytest:main',
        ]
    }
)
