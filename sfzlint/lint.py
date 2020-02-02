# -*- coding: utf-8 -*-

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
    def err_callback(sev, msg, token):
        message = e_format.format(
            path=path, dirname=path.parent, filename=path.name,
            line=token.line, col=token.column,
            sev=sev[0], msg=msg)
        print(message)

    return err_callback


def lint(options):
    path = Path(options.file)
    if not path.exists:
        raise IOError(f'{path} not found')
    if path.is_dir():
        filenames = path.glob('**/*.sfz')
    else:
        filenames = path,
    for filename in filenames:
        lint_file(filename, spec_versions=options.spec_version)


def lint_file(filename, spec_versions=None):
    err_cb = ecb(filename)
    try:
        validate(filename, err_cb=err_cb, spec_versions=spec_versions)
    except (UnexpectedCharacters, UnexpectedToken) as e:
        message = str(e).split('\n', 1)[0]
        err_cb('ERR', message, e)


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
    args = parser.parse_args()
    lint(args)


if __name__ == '__main__':
    main()
