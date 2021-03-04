#!/usr/bin/env python
from setuptools import find_packages, setup


setup(
    name='denkiuc',
    version='0.1',
    description='Denki Unit Commitment Model',
    author='Daniel Marshman',
    author_email='daniel.marshman@protonmail.com',
    url='https://github.com/seagulljim/denki-uc',
    packages=['denkiuc'],
    install_requires=['pulp', 'pandas'],
    license='GNU General Public License v3.0'
)
