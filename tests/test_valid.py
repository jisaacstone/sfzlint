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
        self.assertFalse(errs)
        return sfz

    def test_include(self):
        sfz = self._parse(
            '''
            #include "foobar.sfz"
            ''')
        self.assertIn('foobar.sfz', sfz.includes)

    def test_define(self):
        sfz = self._parse(
            '''
            #define $cool_key 42
            <global> lovel=0 hivel=$cool_key
            ''')
        self.assertEqual(sfz.defines.get('cool_key'), 42)
        self.assertEqual(sfz.headers[0].get('hivel'), 42)

    def test_comments(self):
        sfz = self._parse(
            '''
            /* <global> foo=bar
            #include comment.sfz
            */
            <region>sample=example.wav // baz=biz
            // <group> wat=is
            ''')
        self.assertFalse(sfz.includes)
        region, = sfz.headers
        (k, v), = tuple(region.items())
        self.assertEqual('sample', k)
        self.assertEqual('example.wav', v)

    def test_string(self):
        sfz = self._parse(
            '''
            <region>sw_label=Pseudo_Legato
            ''')
        region, = sfz.headers
        self.assertEqual(region['sw_label'], 'Pseudo_Legato')

    def test_var_types(self):
        sfz = self._parse(
            '''
            <group>
            ampeg_sustain=100
            ampeg_release=0.3
            <region>
            sample=c1.wav
            key=c1
            ''')
        group, region = sfz.headers
        self.assertEqual(group['ampeg_sustain'], 100)
        self.assertEqual(group['ampeg_release'], 0.3)
        self.assertEqual(region['sample'], 'c1.wav')
        self.assertEqual(region['key'], 'c1')
