from setuptools import setup

requirements = [
    'pytest',
    'setuptools',
    'requests',
]

setup(
    name='inzip',
    version='0.0.1',
    description="run tests inside built binary",
    packages=['inzip'],
    include_package_data=True,
    install_requires=requirements,
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'inzip = pytest:main',
        ]
    }
)
