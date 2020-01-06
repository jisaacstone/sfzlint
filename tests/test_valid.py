# -*- coding: utf-8 -*-

from unittest import TestCase
from sfzlint import parser
from inspect import cleandoc as cd


class TestValid(TestCase):
    def _parse(self, docstring):
        sfz, errors, warnings = parser.validate_s(cd(docstring))
        self.assertFalse(errors)
        self.assertFalse(warnings)
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
