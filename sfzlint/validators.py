# -*- coding: utf-8 -*-
from . import opcodes
from . import spec


class Validator:
    def validate(self, token, *args):
        raise NotImplementedError

    def __str__(self):
        return f'<Validator.{self.__class__.__name__}>'


class Any(Validator):
    def validate(self, token, *args):
        return None


class Min(Validator):
    def __init__(self, minimum):
        self.minimum = minimum

    def validate(self, token, *args):
        if token.value < self.minimum:
            return f'{token} less than minimum of {self.minimum}',

    def __str__(self):
        return f'<Validator.Min({self.minimum})>'


class Range(Validator):
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def validate(self, token, *args):
        try:
            if not self.low <= token.value <= self.high:
                return f'{token} not in range {self.low} to {self.high}'
        except TypeError:
            return f'cannot compare {token} with {self.low}, {self.high}'

    def __str__(self):
        return f'<Validator.Range({self.low}, {self.high})>'


class Choice(Validator):
    def __init__(self, choices):
        self.choices = choices

    def validate(self, token, *args):
        if token.value not in self.choices:
            subbed, _ = opcodes.OpcodeIntRepl.sub(token)
            if subbed not in self.choices:
                return f'{token.value} not one of {self.choices}'


class Alias(Validator):
    def __init__(self, name):
        self.name = name

    def validate(self, token, *args):
        return spec.opcodes()[self.name]['validator'].validate(token, *args)

    def __str__(self):
        return f'<Validator.Alias({self.name})>'
