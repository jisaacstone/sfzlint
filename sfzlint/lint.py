# -*- coding: utf-8 -*-

import sys
from argparse import ArgumentParser
from pathlib import Path
from lark.exceptions import UnexpectedCharacters, UnexpectedToken
from .parser import validate
from . import spec


formats = {
    'default': '{path}:{line}:{col}:{sev} {msg}',
    'nopath': '{filename}:{line}:{col}:{sev} {msg}',
}


def ecb(path, e_format=formats['default']):
    def err_callback(sev, msg, token, file_path):
        msg_path = file_path if file_path else path
        message = e_format.format(
            path=msg_path, dirname=path.parent, filename=path.name,
            line=token.line, col=token.column,
            sev=sev[0], msg=msg)
        print(message)

    return err_callback


def lint(options):
    spec_versions = set(options.spec_version) if options.spec_version else None
    path = Path(options.file)
    if not path.exists:
        raise IOError(f'{path} not found')
    if path.is_dir():
        filenames = path.glob('**/*.sfz')
    else:
        filenames = path,
    for filename in filenames:
        config = {
            'spec_versions': spec_versions,
            'file_path': filename,
            'check_includes': options.check_includes,
        }
        lint_file(filename, config=config)


def lint_file(filename, config):
    err_cb = ecb(filename)
    try:
        validate(filename, err_cb=err_cb, config=config)
    except (UnexpectedCharacters, UnexpectedToken) as e:
        message = str(e).split('\n', 1)[0]
        err_cb('ERR', message, e, filename)


def main():
    parser = ArgumentParser(description='linter/validator for sfz files')
    parser.add_argument(
        'file',
        type=Path,
        help='sfz file or directory to recursivly search')
    parser.add_argument(
        '--format', choices=formats.keys(),
        help='error format for output')
    parser.add_argument(
        '--spec-version',
        nargs='*',
        choices=tuple(spec.ver_mapping.values()),
        help='sfz spec to validate against')
    parser.add_argument(
        '-i', '--check-includes',
        action='store_true',
        help='read and check any #include files as well')
    args = parser.parse_args()
    lint(args)


if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        sys.stderr.close()
