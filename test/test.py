#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from sfzlint import validate


if __name__ == '__main__':
    path = Path(__file__).parent / 'example.sfz'
    validated = validate.validate(path)
    print(validated)
