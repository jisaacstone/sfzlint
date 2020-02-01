#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='sfzlint',
    version='0.1',
    description='parser and linter for sfz files written in python',
    author='jisaacstone',
    packages=['sfzlint'],
    package_data={'sfzlint': ['*.ebnf']},
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'sfzlint = sfzlint.lint:main',
            'sfzprint = sfzlint.spec:print_codes',
        ]
    },
    install_requires=[
        'lark-parser>=0.7.8',
    ],
    python_requires='>3.6',
    license='MIT',
)
