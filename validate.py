#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark, Transformer, Discard
from opcodes import validate_opcode_expr, ValidationError, ValidationWarning


class Header(dict):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super(Header, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'Header<{self.name}>{super(Header, self).__repr__()}'


class Note(int):
    '''A midi note name that acts like an int'''

    notes = {'c': 0, 'c#': 1, 'db': 1, 'd': 2, 'd#': 3, 'eb': 3,
             'e': 4, 'f': 5, 'f#': 6, 'gb': 6, 'g': 7, 'g#': 8,
             'ab': 8, 'a': 9, 'a#': 10, 'bb': 10, 'b': 11}

    def __new__(cls, note_name):
        octave = int(note_name[-1])
        key = note_name[:-1].lower()
        note = Note.notes[key] + (octave * 12) + 12  # c1 == 24
        integer = super(Note, cls).__new__(cls, note)
        setattr(integer, 'note_name', note_name)
        return integer

    def __str__(self):
        return self.note_name

    def __repr__(self):
        return f'{super(Note, self).__repr__()}({self})'


def _error(msg, token):
    return {
        'error': msg,
        'line': token.line,
        'column': token.column,
        'near': str(token)}


class SFZValidator(Transformer):
    def __init__(self, *args, **kwargs):
        self.errors = []
        self.warnings = []
        self.current_header = None
        self.defined_variables = {}
        self.imports = []
        super(SFZValidator, self).__init__(*args, **kwargs)

    def header(self, items):
        self.current_header = Header(items[0])
        return self.current_header

    def define_macro(self, items):
        name, value = items
        s_value = self._sanitize_value(value)
        self.defined_variables[str(name)] = s_value
        raise Discard

    def include_macro(self, items):
        value, = items
        self.imports.append(self._sanitize_value(value))
        raise Discard

    def opcode_exp(self, items):
        opcode, value = items
        self._validate_opcode(opcode, value)
        raise Discard

    def start(self, items):
        return {
            'imports': self.imports,
            'defines': self.defined_variables,
            'headers': items,
        }

    def _validate_opcode(self, opcode, value):
        if self.current_header is None:
            self.errors.append(_error('opcode outside of header', opcode))
            raise Discard
        if opcode in self.current_header:
            self.warnings.append(_error('duplicate opcode', opcode))

        s_value = self._sanitize_value(value)
        self.current_header[opcode] = s_value
        try:
            validate_opcode_expr(opcode, value, s_value)
        except ValidationError as e:
            self.errors.append(_error(e.message, e.token))
        except ValidationWarning as e:
            self.warnings.append(_error(e.message, e.token))
        raise Discard

    def _sanitize_value(self, value):
        if value.type == 'ESCAPED_STRING':
            return value[1:-1]
        elif value.type == 'INT':
            return int(value)
        elif value.type == 'FLOAT':
            return float(value)
        elif value.type == 'NOTE_NAME':
            return Note(value)
        elif value.type == 'VARNAME':
            if value not in self.defined_variables:
                self.errors.append(_error('undefined variable', value))
            return self.defined_variables[value]
        return value


def parser(_singleton=[]):
    if not _singleton:
        with open('sfz.ebnf', 'r') as fob:
            _singleton.append(Lark(fob.read(), parser='lalr'))

    return _singleton[0]


def validate(file_path):
    with open(file_path, 'r') as fob:
        file_data = fob.read()
    return validate_s(file_data)


def validate_s(string):
    tree = parser().parse(string)
    validator = SFZValidator(visit_tokens=True)
    transformed = validator.transform(tree)
    print('errors', validator.errors)
    print('warnings', validator.warnings)
    return transformed


if __name__ == '__main__':
    validated = validate('example.sfz')
    print(validated)
