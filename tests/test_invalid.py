# -*- coding: utf-8 -*-

from unittest import TestCase
from sfzlint import parser
from inspect import cleandoc


class TestValid(TestCase):
    def assertEqual(self, aa, bb, *args, **kwargs):
        # handle tokens transparently
        if hasattr(aa, 'value'):
            aa = aa.value
        if hasattr(bb, 'value'):
            bb = bb.value
        return super(TestValid, self).assertEqual(aa, bb, *args, **kwargs)

    def _parse(self, docstring):
        errs = []

        def err_cb(*args):
            errs.append(args)

        sfz = parser.validate_s(cleandoc(docstring), err_cb=err_cb)
        self.assertTrue(errs)
        return sfz, errs

    def test_dupe_global(self):
        sfz, errs = self._parse(
            '''
            <global> lovel=0
            <region> sample=kick.wav
            <global> lovel=2
            ''')
        (_sev, _msg, token), = errs
        self.assertEqual(token, 'global')

    def test_unknown_opcode(self):
        sfz, errs = self._parse(
            '''
            <region>foo=bar
            ''')
        (_sev, _msg, token), = errs
        self.assertEqual(token, 'foo')
        region, = sfz.regions
        self.assertEqual(region['foo'], 'bar')

    def test_opcode_without_header(self):
        sfz, errs = self._parse(
            '''
            sample=out of my head.wav
            <region> key=db3
            ''')
        (_sev, _msg, token), = errs
        self.assertEqual(token, 'sample')
