# -*- coding: utf-8 -*-
from . import opcodes
from . import spec


class Validator:
    def validate(self, value, *args):
        raise NotImplementedError

    def __str__(self):
        return f'<Validator.{self.__class__.__name__}()>'


class Any(Validator):
    def validate(self, value, *args):
        return None


class Min(Validator):
    def __init__(self, minimum):
        self.minimum = minimum

    def validate(self, value, *args):
        if value < self.minimum:
            return f'{value} less than minimum of {self.minimum}',

    def __str__(self):
        return f'<Validator.Min({self.minimum})>'


class Range(Validator):
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def validate(self, value, *args):
        try:
            if not self.low <= value <= self.high:
                return f'{value} not in range {self.low} to {self.high}'
        except TypeError:
            return f'cannot compare {value} with {self.low}, {self.high}'

    def __str__(self):
        return f'<Validator.Range({self.low},{self.high})>'


class Choice(Validator):
    def __init__(self, choices):
        self.choices = choices

    def validate(self, value, *args):
        if value not in self.choices:
            subbed = opcodes.OpcodeIntRepl.sub_str(value)
            if subbed not in self.choices:
                return f'{value} not one of {self.choices}'


class Alias(Validator):
    def __init__(self, name):
        self.name = name

    def validate(self, value, *args):
        opc = spec.opcodes()[self.name].get('value')
        if opc and 'validator' in opc:
            return opc['validator'].validate(value, *args)

    def __str__(self):
        return f'<Validator.Alias({self.name})>'
