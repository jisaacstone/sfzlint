#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from pathlib import Path

# remove the .pickle cache files
# I'm lazy to hook into the setup functions
for pfile in Path(__file__).parent.rglob('*.pickle'):
    pfile.unlink()

setup(
    name='sfzlint',
    version='0.1.2',
    description='parser and linter for sfz files written in python',
    author='jisaacstone',
    packages=['sfzlint'],
    package_data={'sfzlint': ['*.ebnf']},
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'sfzlint = sfzlint.cli:sfzlint',
            'sfzlist = sfzlint.cli:sfzlist',
        ]
    },
    install_requires=[
        'lark-parser>=0.7.8',
    ],
    python_requires='>3.6',
    license='MIT',
)
