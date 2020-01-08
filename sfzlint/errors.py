# -*- coding: utf-8 -*-


class ValidationException(Exception):
    def __init__(self, message, token):
        self.message = message
        self.token = token


ValidationError = type('ValidationError', (ValidationException,), {})
ValidationWarning = type('ValidationWarning', (ValidationException,), {})
