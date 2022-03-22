# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from argparse import ArgumentParser
from . import spec, parser, lint, opcodes, settings


def print_codes(search=None, filters=None, printer=print):
    for o in spec.opcodes().values():
        print_code(o, search, filters, printer)


def print_code(code, search=None, filters=None, printer=print):
    if search and search not in code['name']:
        return
    if filters:
        if not all(code.get(k) == v for k, v in filters):
            return

    data = [
        code.get('name', '').ljust(25, ' '),
        code.get('ver', '').ljust(8, ' '),
        str(code.get('validator', ''))[11:-1].ljust(25, ' ')]
    if 'modulates' in code:
        data.append(f'modulates={code["modulates"]}')

    printer('\t'.join(data))


def print_codes_in_path(path, search, filters, printer=print):
    codes = set()
    for fp in path.rglob('*.sfz'):
        try:
            with fp.open() as fob:
                contents = fob.read() + '\n'
                parsed = parser.parser().parse(contents)
                validator = parser.SFZValidator(config={'file_path': fp})
                validator.transform(parsed)
                sfz = validator.config.sfz
                to_check = {str(k): k for h in sfz.headers for k in h}
                for raw_oc in to_check.values():
                    try:
                        opcode, _ = opcodes.OpcodeIntRepl.sub(raw_oc)
                    except Exception as e:
                        print(e)
                        opcode = raw_oc
                    codes.add(str(opcode))
        except Exception as e:
            sys.stderr.write(f'Error checking {fp}: {e}')
    op_data = spec.opcodes()

    def unknown(code):
        return {'name': code, 'ver': 'unknown'}

    for code in codes:
        data = op_data.get(code, unknown(code))
        print_code(data, search, filters, printer)


def sfzlist(printer=print):
    '''Entry point for the sfzlist cli command'''

    def eq_filter(string):
        k, v = string.split('=')
        return (k, v)

    parser = ArgumentParser(
        description='list know opcodes and metadata',
        epilog='example: sfzlist --filter ver=v2')
    parser.add_argument(
        '--search', '-s',
        help='seach name by substring')
    parser.add_argument(
        '--filter', '-f',
        dest='filters',
        nargs='*',
        type=eq_filter,
        help='filter fields by "key=value"')
    parser.add_argument(
        '--path', '-p',
        type=Path,
        help='print only opcodes found in the sfz file(s) in PATH')
    parser.add_argument(
        '--no-pickle',
        action='store_true',
        help='do not use the pickle cache (for testing)')
    args = parser.parse_args()
    if not args.no_pickle:
        settings.pickle = True
        1/0
    try:
        if args.path:
            print_codes_in_path(args.path, args.search, args.filters, printer)
        else:
            print_codes(args.search, args.filters, printer)
    except BrokenPipeError:
        sys.stderr.close()


def sfzlint():
    settings.pickle = True
    return lint.main()
