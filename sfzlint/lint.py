# -*- coding: utf-8 -*-

import re
import sys
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from pathlib import Path
from lark.exceptions import UnexpectedCharacters, UnexpectedToken
from .parser import validate, SFZ, SFZValidatorConfig
from . import spec, settings


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
        config = SFZValidatorConfig(
            spec_versions=spec_versions,
            file_path=filename,
            check_includes=options.check_includes,
        )
        if options.rel_path:
            config.rel_path = options.rel_path
        if filename.suffix == '.xml':
            lint_xml(filename, config)
        else:
            lint_sfz(filename, config=config)


def lint_xml(filename, config):
    with open(filename) as fob:
        xml = fob.read()
    # xml is "malformed" because it lacks a single root element
    # solution is to wrap it in a "root" tag
    tree = ET.fromstring(
        re.sub(r"(<\?xml[^>]+\?>)", r"\1<root>", xml) + "</root>")
    defines = {
        d.attrib['name'][1:]: d.attrib['value']
        for d in tree.findall('.//Define')}
    for ae in tree.findall('.//AriaElement'):
        ae_path = filename.parent / ae.attrib['path']
        config.file_name = ae_path
        config.rel_path = ae_path.parent
        config.check_includes = True  # Always check on program .xml
        if defines:
            config.sfz = SFZ(defines=defines)
        lint_sfz(ae_path, config)


def lint_sfz(filename, config):
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
    parser.add_argument(
        '--rel-path',
        help='validate includes and sample paths relative to this path')
    parser.add_argument(
        '--no-pickle',
        action='store_true',
        help='do not use the pickle cache (for testing)')
    args = parser.parse_args()
    settings.pickle = not args.no_pickle
    lint(args)


if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        sys.stderr.close()
