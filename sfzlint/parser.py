# -*- coding: utf-8 -*-

from lark import Lark, Transformer, Token
from .opcodes import validate_opcode_expr, ValidationError, ValidationWarning


class Header(dict):
    '''A dictionary with a name

    used to store opcode pairs under their header tag
    e.g. <global>hivel=25 -> Header<global>{'hivel': 25}
    '''
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super(Header, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'Header<{self.name}>{super(Header, self).__repr__()}'


class Note(int):
    '''A midi note name that acts like an int.

    This exists so that notes can be compared in the Range() validators
    '''

    notemap = {'c': 0, 'c#': 1, 'db': 1, 'd': 2, 'd#': 3, 'eb': 3,
               'e': 4, 'f': 5, 'f#': 6, 'gb': 6, 'g': 7, 'g#': 8,
               'ab': 8, 'a': 9, 'a#': 10, 'bb': 10, 'b': 11}

    def __new__(cls, note_name):
        octave = int(note_name[-1])
        key = note_name[:-1].lower()
        note = Note.notemap[key] + (octave * 12) + 12  # c1 == 24
        integer = super(Note, cls).__new__(cls, note)
        setattr(integer, 'note_name', note_name)
        return integer

    def __eq__(self, other):
        '''Note('c1') == 'c1' and Note('c1') == 24'''
        if self.note_name == other:
            return True
        return super(Note, self).__eq__(other)

    def __ne__(self, other):
        if self.note_name == other:
            return False
        return super(Note, self).__ne__(other)

    def __str__(self):
        return self.note_name

    def __repr__(self):
        return f'{super(Note, self).__repr__()}({self})'


class SFZ:
    def __init__(self, *headers, defines=None, includes=None):
        self.headers = list(headers)
        self.defines = {} if defines is None else defines
        self.includes = [] if includes is None else includes

    def iterstr(self):
        # TODO: defines: keep them or no?
        for inc in self.includes:
            yield f'#include "{inc}"\n'
        for header in self.headers:
            yield f'<{header.name}>\n'
            for opcode, value in header.items():
                yield f'{opcode}={value}\n'

    def __str__(self):
        def iter_with_cutoff(cutoff=20):
            for index, string in enumerate(self.iterstr()):
                if index == cutoff:
                    yield '...'
                    raise StopIteration
                yield string

        return ''.join(iter_with_cutoff())


class SFZValidator(Transformer):
    '''Turns the generated syntax tree into an instance of SFZ'''

    def _err(self, msg, token):
        if self.err_cb:
            self.err_cb('ERR', msg, token)

    def _warn(self, msg, token):
        if self.err_cb:
            self.err_cb('WARN', msg, token)

    def __init__(self, err_cb=None, *args, **kwargs):
        self.current_header = None
        self.sfz = SFZ()
        self.err_cb = err_cb
        super(SFZValidator, self).__init__(*args, **kwargs)

    def header(self, items):
        self.current_header = Header(items[0])
        self.sfz.headers.append(self.current_header)

    def define_macro(self, items):
        name, value = items
        s_value = self._sanitize_token(value)
        self.sfz.defines[str(name)] = s_value

    def include_macro(self, items):
        token, = items
        self.sfz.includes.append(self._sanitize_token(token))

    def opcode_exp(self, items):
        opcode, value = items
        self._validate_opcode(opcode, value)

    def start(self, items):
        return self.sfz

    def _validate_opcode(self, opcode, value):
        if self.current_header is None:
            self._err(f'opcode outside of header ({opcode})', opcode)
            return
        if opcode in self.current_header:
            self._warn('duplicate opcode', opcode)

        token = self._sanitize_token(value)
        self.current_header[opcode] = token
        try:
            validate_opcode_expr(opcode, token)
        except ValidationError as e:
            self._err(e.message, e.token)
        except ValidationWarning as e:
            self._warn(e.message, e.token)

    def _update_tok(self, token, value):
        # token.update is not released yet (lark v7.8)
        return Token.new_borrow_pos(
            token.type, value, token)

    def _sanitize_token(self, token):
        if token.type == 'ESCAPED_STRING':
            return self._update_tok(token, token[1:-1])
        elif token.type == 'INT':
            return self._update_tok(token, int(token))
        elif token.type == 'FLOAT':
            return self._update_tok(token, float(token))
        elif token.type == 'NOTE_NAME':
            return self._update_tok(token, Note(token))
        elif token.type == 'VARNAME':
            if token not in self.sfz.defines:
                self._err('undefined variable', token)
            return self._update_tok(token, self.sfz.defines[token].value)
        return token


def parser(_singleton=[]):
    '''Returns a Lark parser using the grammar in sfz.ebnf'''
    if not _singleton:
        _singleton.append(
            Lark.open('sfz.ebnf', rel_to=__file__, parser='lalr'))

    return _singleton[0]


def validate(file_path, *args, **kwargs):
    with open(file_path, 'r') as fob:
        # can't use the file stream because the lexer calls len()
        file_data = fob.read()
    return validate_s(file_data, *args, **kwargs)


def validate_s(string, *args, **kwargs):
    tree = parser().parse(string)
    validator = SFZValidator(*args, **kwargs)
    transformed = validator.transform(tree)
    return transformed
