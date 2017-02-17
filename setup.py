#!/usr/bin/env python3

from setuptools import setup
import unittest

def physpy_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite

setup(
    name='physpy',
    version='0.1.0',
    description='A SymPy-based library for calculating the error percentage for measured values',
    url='http://github.com/KolesnichenkoDS/PhysPy',
    author='Daniil Kolesnichenko',
    author_email='d.s.kolesnichenko@ya.ru',
    license='MIT',
    packages=['physpy'],
    install_requires=[
        'pdoc',
        'sympy',
    ],
    test_suite='setup.physpy_test_suite',
)

import os, pdoc

if not os.path.exists('docs'):
    os.makedirs('docs')

with open('docs/index.html', 'w') as f:
    f.write(pdoc.html('physpy', source=False))
