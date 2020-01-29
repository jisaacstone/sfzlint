# -*- coding: utf-8 -*-

from unittest import TestCase
from sfzlint import parser
from inspect import cleandoc


class TestInvalid(TestCase):
    def assertEqual(self, aa, bb, *args, **kwargs):
        # handle tokens transparently
        if hasattr(aa, 'value'):
            aa = aa.value
        if hasattr(bb, 'value'):
            bb = bb.value
        return super(TestInvalid, self).assertEqual(aa, bb, *args, **kwargs)

    def _parse(self, docstring, **kwargs):
        errs = []

        def err_cb(*args):
            errs.append(args)

        sfz = parser.validate_s(cleandoc(docstring), err_cb=err_cb, **kwargs)
        self.assertTrue(errs)
        return sfz, errs

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

    def test_invalid_version(self):
        sfz, errs = self._parse(
            '''
            <group>note_offset=12
            ''', spec_version='v1')
        (_sev, _msg, token), = errs
        self.assertEqual(token, 'note_offset')
