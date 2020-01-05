#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark
with open('sfz.ebnf', 'r') as fob:
    sfz_parser = Lark(fob.read())

with open('example.sfz', 'r') as fob:
    tree = sfz_parser.parse(fob.read())

print(tree.pretty())
