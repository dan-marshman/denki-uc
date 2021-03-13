#!/usr/bin/env python
from setuptools import find_packages, setup
import os

datafiles = [(d, [os.path.join(d, f) for f in files]) for d, folders, files in os.walk('examples')]

setup(
    name='denkiuc',
    version='0.1',
    description='Denki Unit Commitment Model',
    author='Daniel Marshman',
    author_email='daniel.marshman@protonmail.com',
    url='https://github.com/dan-marshman/denki-uc',
    packages=find_packages(),
    data_files=datafiles,
    install_requires=['pulp', 'pandas', 'numpy'],
    license='GNU General Public License v3.0'
)
