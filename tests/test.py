#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from sfzlint import parser


if __name__ == '__main__':
    path = Path(__file__).parent / 'example.sfz'
    validated = parser.validate(path)
    print(validated)
