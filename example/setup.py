from setuptools import setup

requirements = [
    'Flask',
    'gunicorn',
    'gevent==1.1rc3',
]

setup(
    name='myip',
    version='0.0.1',
    description="show my ip",
    packages=['myip'],
    include_package_data=True,
    install_requires=requirements,
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'myip = myip.myip:main',
        ]
    }
)
