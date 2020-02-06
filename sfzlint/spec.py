# -*- coding: utf-8 -*-

import yaml
from argparse import ArgumentParser
from pathlib import Path
from numbers import Real  # int or float
from . import validators


ver_mapping = {
    'SFZ v1': 'v1',
    'SFZ v2': 'v2',
    'ARIA': 'aria',
    'LinuxSampler': 'linuxsampler',
    'Cakewalk': 'cakewalk',
    'Cakewalk SFZ v2': 'cakewalk v2',  # unimplementd by any player
}


type_mapping = {
    'integer': int,
    'float': Real,
    'string': str,
}


class TuneValidator(validators.Validator):
    def validate(self, token, spec_versions, *args):
        if not spec_versions or 'aria' in spec_versions:
            return validators.Range(-2400, 2400).validate(token)
        return validators.Range(-100, 100).validate(token)


class VarTargetValidator(validators.Validator):
    def __init__(self, meta):
        self.choice_validator = meta['validator']

    def validate(self, token, _, subs):
        return self.choice_validator.validate(subs['target'])


overrides = {
    'tune':
        {'ver': 'v1', 'type': int,
         'validator': TuneValidator()},
    'type':
        {'ver': 'aria', 'type': str, 'header': 'effect',
         'validator': validators.Any()},
}


def _override(ops):
    for k, v in overrides.items():
        ops[k] = v
    # the choices in the yml are 'target' choices not value choices
    ops['varNN_target']['validator'] = VarTargetValidator(ops['varNN_target'])
    del ops['varNN_target']['type']
    return ops


def _import(cache=[]):
    if not cache:
        with (Path(__file__).parent / 'syntax.yml').open() as syn_yml:
            syntax = yaml.load(syn_yml, Loader=yaml.SafeLoader)
        cache.append(syntax)
    return cache[-1]


def _extract():
    syn = _import()
    cat = syn['categories']
    ops = {o['name']: o for o in _extract_op(cat)}
    return ops


def opcodes(key=None, cache=[]):
    if not cache:
        ops = _extract()
        cache.append(_override(ops))
    return cache[-1]


def _extract_op(categories):
    for category in categories:
        op = category.get('opcodes')
        if op:
            yield from _iter_ops(op)
        types = category.get('types')
        if types:
            yield from _extract_op(types)


def _iter_ops(opcodes):
    for opcode in opcodes:
        yield from op_to_validator(opcode)


def op_to_validator(op_data, **kwargs):
    valid_meta = dict(
        name=op_data['name'],
        ver=ver_mapping[op_data['version']],
        **kwargs)
    data_value = op_data.get('value')
    if data_value:
        if 'type_name' in data_value:
            valid_meta['type'] = type_mapping[data_value['type_name']]
        valid_meta['validator'] = _validator(data_value)
    else:
        valid_meta['validator'] = validators.Any()
    yield valid_meta
    for alias in op_data.get('alias', []):
        alias_meta = {
            'validator': validators.Alias(op_data['name']),
            'name': alias['name']}
        if 'version' in alias:
            alias_meta['ver'] = ver_mapping[alias['version']],
        else:
            alias_meta['ver'] = valid_meta['ver']
        yield alias_meta
    if 'modulation' in op_data:
        for mod_type, modulations in op_data['modulation'].items():
            if isinstance(modulations, list):  # some are just checkmarks
                for mod in modulations:
                    yield from op_to_validator(
                        mod, modulates=op_data['name'], mod_type=mod_type)


def _validator(data_value):
    if 'min' in data_value:
        if 'max' in data_value:
            if not isinstance(data_value['max'], Real):
                # string value, eg "SampleRate / 2"
                return validators.Min(data_value['min'])
            return validators.Range(data_value['min'], data_value['max'])
        return validators.Min(data_value['min'])
    if 'options' in data_value:
        return validators.Choice(
            [o['name'] for o in data_value['options']])
    return validators.Any()


def print_codes(search=None, filters=None, printer=print):
    order = {
        'name': 0, 'ver': 1, 'validator': 2, 'mod_type': 3, 'modulates': 4}

    def key(o_tup):
        return order.get(o_tup[0], 10)

    syn = _import()
    cat = syn['categories']
    for o in _extract_op(cat):
        if search and search not in o['name']:
            continue
        if filters:
            if not all(o.get(k) == v for k, v in filters):
                continue
        printer(', '.join(
            f'{k}={v}' for k, v in sorted(o.items(), key=key)))


def sfzlist():
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
    args = parser.parse_args()
    print_codes(args.search, args.filters)
