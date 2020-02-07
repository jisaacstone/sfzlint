# -*- coding: utf-8 -*-

from pathlib import Path
from collections import ChainMap
from lark import Lark, Transformer, Token
from . import opcodes
from .errors import ValidationError, ValidationWarning
from .headers import Header, HeaderList


def update_token(token, value):
    # token.update is not released yet (lark v7.8)
    return Token.new_borrow_pos(
        token.type, value, token)


class Note(int):
    '''A midi note name that acts like an int.

    This exists so that notes can be compared in the Range() validators
    '''

    notemap = {'c': 0, 'c#': 1, 'db': 1, 'd': 2, 'd#': 3, 'eb': 3,
               'e': 4, 'f': 5, 'f#': 6, 'gb': 6, 'g': 7, 'g#': 8,
               'ab': 8, 'a': 9, 'a#': 10, 'bb': 10, 'b': 11}

    def __new__(cls, note_name):
        try:
            octave = int(note_name[-1])
            key = note_name[:-1].lower()
        except (ValueError, KeyError):
            raise ValueError(f'could not convert string to Note: {note_name}')
        try:
            note = Note.notemap[key] + (octave * 12) + 12  # c1 == 24
        except KeyError:
            raise ValueError(f'unknown key: {key}')
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
        self.headers = HeaderList(*headers)
        self.defines = {} if defines is None else defines
        self.includes = [] if includes is None else includes

    def iterstr(self):
        for inc in self.includes:
            yield f'#include "{inc}"\n'
        for header in self.headers:
            yield f'<{header.name}>\n'
            for opcode, value in header.items():
                yield f'{opcode}={value}\n'

    # Don't know if I like this or not. Feel there is a better approach
    # Just can't think of it at the moment
    @property
    def regions(self):
        return [h for h in self.headers if h.token == 'region']

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
    default_config = {
        'warn_undefined_var': False,
    }

    def _err(self, msg, token):
        if self.err_cb:
            self.err_cb('ERR', msg, token, self.file_path)

    def _warn(self, msg, token):
        if self.err_cb:
            self.err_cb('WARN', msg, token, self.file_path)

    def __init__(self, err_cb=None, config=None, *args, **kwargs):
        self.config = ChainMap(config or {}, self.default_config)
        self.current_header = None
        self.file_path = kwargs.pop('file_path', None)
        self.sfz = SFZ()
        self.err_cb = err_cb
        super(SFZValidator, self).__init__(*args, **kwargs)

    def header(self, items):
        header = Header(items[0])
        self._validate_header(header)
        try:
            self.sfz.headers.append(header)
            self.current_header = header
        except AttributeError as e:
            self._err(e.args[0], items[0])

    def define_macro(self, items):
        varname, value = items
        s_value = self._sanitize_token(value)
        self.sfz.defines[varname.value] = s_value

    def include_macro(self, items):
        token, = items
        sanitized = self._sanitize_token(token)
        if self.file_path:
            self._load_include(sanitized)
        self.sfz.includes.append(sanitized)

    def opcode_exp(self, items):
        opcode, value = items
        self._validate_opcode(opcode, value)

    def start(self, items):
        return self.sfz

    def _load_include(self, rel_path):
        path = Path(self.file_path).parent / rel_path
        if not path.is_file():
            self._err('could not load include, file not found', rel_path)
        else:
            old_file = self.file_path
            self.file_path = path
            with path.open() as fob:
                contents = fob.read()
                tree = parser().parse(contents)
                self.transform(tree)
            self.file_path = old_file

    def _validate_header(self, header):
        if self.config.get('spec_versions'):
            if header.version not in self.config['spec_versions']:
                self._warn(f'header spec {header.version} not in '
                           f'{self.config["spec_versions"]} ({header.token})',
                           header.token)

    def _validate_opcode(self, opcode, value):
        if self.current_header is None:
            self._err(f'opcode outside of header ({opcode})', opcode)
            return
        if '$' in opcode:
            pre, post = opcode.split('$', 1)
            replaced = self._varreplace('$' + post)
            opcode = update_token(opcode, f'{pre}{replaced}')
        if opcode in self.current_header:
            self._warn('duplicate opcode', opcode)

        opcode = update_token(opcode, opcode.lower())
        token = self._sanitize_token(value)
        self.current_header[opcode] = token
        try:
            opcodes.validate_opcode_expr(
                opcode, token, self.config.get('spec_versions'))
        except ValidationError as e:
            self._err(e.message, e.token)
        except ValidationWarning as e:
            self._warn(e.message, e.token)

    def _varreplace(self, token):
        value = token[1:]
        if value not in self.sfz.defines:
            if self.config['warn_undefined_var']:
                self._err('undefined variable', token)
            return token
        else:
            return self.sfz.defines[value].value

    def _sanitize_token(self, token):
        if token[0] == '"' and token[-1] == '"':
            # qoated string
            return update_token(token, token[1:-1])
        elif token[0] == '$':
            # defined variable
            return update_token(token, self._varreplace(token))
        for converter in (int, float, Note):
            # numerics
            try:
                return update_token(token, converter(token))
            except ValueError:
                pass
        # string
        return update_token(token, token.strip())


def parser(_singleton=[]):
    '''Returns a Lark parser using the grammar in sfz.lark'''
    if not _singleton:
        _singleton.append(
            Lark.open('sfz.lark', rel_to=__file__, parser='lalr'))

    return _singleton[0]


def validate(file_path, *args, **kwargs):
    with open(file_path, 'r') as fob:
        # can't use the file stream because the lexer calls len()
        file_data = fob.read()
    return validate_s(file_data, *args, **kwargs)


def validate_s(string, *args, **kwargs):
    tree = parser().parse(string + '\n')
    validator = SFZValidator(*args, **kwargs)
    transformed = validator.transform(tree)
    return transformed
