# -*- coding: utf-8 -*-

import os
import pickle
from functools import lru_cache
from pathlib import Path
from numbers import Real  # int or float
import yaml
from . import validators


ver_mapping = {
    None: 'unknown',
    'SFZ v1': 'v1',
    'SFZ v2': 'v2',
    'ARIA': 'aria',
    'LinuxSampler': 'linuxsampler',
    'Cakewalk': 'cakewalk',
    'Cakewalk SFZ v2': 'cakewalk_v2',  # unimplementd by any player
}


type_mapping = {
    'integer': int,
    'float': Real,
    'string': str,
}

# there will be repetitive calls to listdir
@lru_cache(maxsize=32)
def listdir(path):
    return set(os.listdir(path))


# special-purpose validators
class TuneValidator(validators.Validator):
    def validate(self, value, config, *args):
        spec_versions = config.spec_versions
        if not spec_versions or 'aria' in spec_versions:
            return validators.Range(-2400, 2400).validate(value)
        return validators.Range(-100, 100).validate(value)


class SampleValidator(validators.Validator):
    def validate(self, value, config, *args):
        try:
            if value[0] == '*':  # built-in *sine, *square, etc sounds
                return
            if not config.rel_path:
                return
            sampath = Path(value.replace('\\', '/'))
        except TypeError:
            return f'not a valid path "{value}"'
        try:
            resolved = (config.rel_path / sampath).resolve(strict=True)
        except FileNotFoundError:
            return f'file not found "{value}"'

        parts = reversed(sampath.parts)
        for part in parts:
            if part == '..':  # there is a limit to our cleverness
                break
            resolved = resolved.parent
            if part not in listdir(resolved):
                return f'case does not match file for "{value}"'


class CurveCCValidator(validators.Validator):
    def validate(self, value, config, *args):
        if value < 0:
            return 'negative curve_index'
        if value < 7:
            # likely a default or built-in curve, no check
            return
        if config.sfz and value not in config.sfz.curves:
            return 'no corresponding curve_index found'


overrides = {
    ('tune', 'value', 'validator'): TuneValidator(),
    ('sample', 'value', 'validator'): SampleValidator(),
    ('varNN_target', 'value',  'type'): object,
    ('*_mod', 'target'): {'validator': validators.Choice(
        ('delay', 'delay_beats', 'stop_beats', 'offset', 'pitch',
         'tune', 'volume', 'amplitude', 'cutoff', 'resonance',
         'fil_gain', 'cutoff2', 'resonance2', 'fil2_gain', 'pan',
         'position', 'width', 'bitred', 'decim'))},
    # if a label is parsed as an int by the lexer that is OK
    ('label_ccN', 'value', 'type'): object,
    ('global_label', 'value', 'type'): object,
    ('master_label', 'value', 'type'): object,
    ('group_label', 'value', 'type'): object,
    ('region_label', 'value', 'type'): object,
    ('sw_label', 'value', 'type'): object,
}


def _override(ops):
    for keys, override in overrides.items():
        opp = ops
        for key in keys[:-1]:
            opp = opp[key]
        opp[keys[-1]] = override

    # the choices in the yml are 'target' choices not value choices
    ops['varNN_target']['target'] = ops['varNN_target'].pop('value')
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
        ver=ver_mapping[op_data.get('version')],
        **kwargs)
    _extract_vdr_meta(op_data, valid_meta)
    yield valid_meta
    for alias in op_data.get('alias', []):
        alias_meta = {
            'name': alias['name'],
            'value': {'validator': validators.Alias(op_data['name'])},
        }
        if 'version' in alias:
            alias_meta['ver'] = ver_mapping[alias['version']]
        else:
            alias_meta['ver'] = valid_meta['ver']
        yield alias_meta
    if 'modulation' in op_data:
        for mod_type, modulations in op_data['modulation'].items():
            if isinstance(modulations, list):  # some are just checkmarks
                for mod in modulations:
                    yield from op_to_validator(
                        mod, modulates=op_data['name'], mod_type=mod_type)


def _extract_vdr_meta(op_data, valid_meta):
    for v_key in ('value', 'index'):
        if v_key in op_data:
            if v_key not in valid_meta:
                valid_meta[v_key] = {}
            valid_meta[v_key]['validator'] = _validator(op_data[v_key])
            if 'type' in op_data[v_key]:
                valid_meta[v_key]['type'] = type_mapping[
                    op_data[v_key]['type_name']]


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


def _pickled(name, fn):
    p_file = Path(__file__).parent / f'{name}.pickle'
    if not p_file.exists():
        data = fn()
        with p_file.open('wb') as fob:
            pickle.dump(data, fob)
    else:
        with p_file.open('rb') as fob:
            data = pickle.load(fob)
    return data


# pickling as cache cuts script time by ~400ms on my system
opcodes = _pickled('opcides', lambda: _override(_extract()))
cc_opcodes = {k for k in opcodes if 'cc' in k and 'curvecc' not in k}
