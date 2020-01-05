#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark, Transformer, Discard


class Header(dict):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super(Header, self).__init__(*args, **kwargs)


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
        s_value = self._sanitize_value(value)
        if not self.current_header:
            self.errors.append(_error('opcode outside of header', opcode))
        if opcode in self.current_header:
            self.warnings.append(_error('duplicate opcode', opcode))
        self.current_header[opcode] = s_value

    def _sanitize_value(self, value):
        if value.type == 'ESCAPED_STRING':
            return value[1:-1]
        elif value.type == 'INT':
            return int(value)
        elif value.type == 'FLOAT':
            return float(value)
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
    return transformed


if __name__ == '__main__':
    validated = validate('example.sfz')
    print(validated)
