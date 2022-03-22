#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from pathlib import Path

try:
    import appdirs
except Exception:
    pass  # not installed yet probably
else:
    # remove the .pickle cache files
    # I'm lazy to hook into the setup functions
    user_cache_dir = Path(appdirs.user_cache_dir("sfzlint", "jisaacstone"))
    for pfile in user_cache_dir.rglob('*.pickle'):
        pfile.unlink()

setup(
    name='sfzlint',
    version='0.1.4',
    description='parser and linter for sfz files written in python',
    author='jisaacstone',
    packages=['sfzlint'],
    package_data={'sfzlint': ['*.ebnf','*.yml','*.lark']},
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'sfzlint = sfzlint.cli:sfzlint',
            'sfzlist = sfzlint.cli:sfzlist',
        ]
    },
    install_requires=[
        'appdirs',
        'lark-parser>=0.7.8',
        'pyyaml>=6.0.0'
    ],
    python_requires='>3.6',
    license='MIT',
)
