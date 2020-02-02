# -*- coding: utf-8 -*-

import yaml
from pathlib import Path
from numbers import Real  # int or float
from .validators import Any, Min, Range, Choice, Alias, Validator


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


class TuneValidator(Validator):
    def validate(self, token, spec_versions, *args):
        if not spec_versions or 'aria' in spec_versions:
            return Range(-2400, 2400).validate(token)
        return Range(-100, 100).validate(token)


class VarTargetValidator(Validator):
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
         'validator': Any()},
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
        valid_meta['validator'] = Any()
    yield valid_meta
    for alias in op_data.get('alias', []):
        alias_meta = {
            'ver': ver_mapping[alias['version']],
            'validator': Alias(op_data['name']),
            'name': alias['name']}
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
                return Min(data_value['min'])
            return Range(data_value['min'], data_value['max'])
        return Min(data_value['min'])
    if 'options' in data_value:
        return Choice(
            [o['name'] for o in data_value['options']])
    return Any()


def print_codes(printer=print):
    syn = _import()
    cat = syn['categories']
    for o in _extract_op(cat):
        printer(', '.join(f'{k}={v}' for k, v in o.items()))
