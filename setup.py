#!/usr/bin/python
from setuptools import setup, find_packages

setup(
    name='vr.imager',
    namespace_packages=['vr'],
    version='1.2',
    author='Brent Tubbs',
    author_email='brent.tubbs@gmail.com',
    url='https://bitbucket.org/yougov/vr.imager',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'vr.runners>=2.8,<3',
        'jaraco.ui',
        'path.py>=7.2',
        'vr.common>=4.3,<5dev',
    ],
    entry_points={
        'console_scripts': [
            'vimage = vr.imager.command:invoke',
        ],
    },
    setup_requires=[
        'setuptools_scm',
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
    description='Command line tool to create system image tarballs.',
)
