from setuptools import setup

requirements = [
    'Flask',
    'gunicorn',
    'gevent',
]

setup(
    name='example',
    version='0.0.1',
    description="show my ip",
    py_modules=['myip'],
    include_package_data=True,
    install_requires=requirements,
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'myip = myip:main',
        ]
    }
)
