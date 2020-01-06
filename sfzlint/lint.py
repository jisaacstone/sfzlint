#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .parser import validate
from argparse import ArgumentParser
from pathlib import Path


def ecb(filename=''):
    def err_callback(sev, msg, token):
        print(f'{filename}:{token.line}:{token.column}:{sev[0]} {msg}')

    return err_callback


def main():
    parser = ArgumentParser()
    parser.add_argument('filename', type=Path)
    args = parser.parse_args()
    validate(args.filename, err_cb=ecb(args.filename))


if __name__ == '__main__':
    main()
