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

        sfz = parser.validate_s(
            cleandoc(docstring), err_cb=err_cb, config=kwargs)
        self.assertTrue(errs)
        return sfz, errs

    def test_unknown_opcode(self):
        sfz, errs = self._parse(
            '''
            <region>foo=bar
            ''')
        (_sev, _msg, token, _), = errs
        self.assertEqual(token, 'foo')
        region, = sfz.regions
        self.assertEqual(region['foo'], 'bar')

    def test_opcode_without_header(self):
        _, errs = self._parse(
            '''
            sample=out of my head.wav
            <region> key=db3
            ''')
        (_sev, _msg, token, _), = errs
        self.assertEqual(token, 'sample')

    def test_invalid_version(self):
        _, errs = self._parse(
            '''
            <group>note_offset=12
            ''', spec_versions=['v1'])
        (_sev, _msg, token, _), = errs
        self.assertEqual(token, 'note_offset')

    def test_version_validator(self):
        _, errs = self._parse(
            '''
            <region>
            tune=-400
            ''', spec_versions=['v1'])
        (_sev, _msg, token, _), = errs
        self.assertEqual(token, -400)

    def test_cakewalk_unimplemented(self):
        _, errs = self._parse(
            '''
            <region>
            noise_stereo=on
            ''')
        (sev, _msg, token, _), = errs
        self.assertEqual(token, 'noise_stereo')
        self.assertEqual(sev, 'WARN')

    def test_unknown_cc_format(self):
        _, errs = self._parse(
            '''
            <control>
            labelcc5=awesome
            ''')
        (sev, msg, token, _), = errs
        self.assertEqual(token, 'labelcc5')
        self.assertEqual(sev, 'WARN')
        self.assertIn('undocumented alias', msg)

    def test_bad_control_code(self):
        _, errs = self._parse(
            '''
            <group>amplitude_oncc420=75
            ''')
        (_sev, _, token, _), = errs
        self.assertEqual(token, 'amplitude_oncc420')
