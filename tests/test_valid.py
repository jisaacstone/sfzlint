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

    def test_silence_sample(self):
        sfz = self._parse(
            '''
            <group>key=29 sample=*silence
            ''')
        self.assertEqual(sfz.headers[0]['sample'], '*silence')

    def test_label(self):
        sfz = self._parse(
            '''
            <global> global_label=kick
            amplitude_oncc20=75
            master_label=18x18'' kick

            <master> key=35
            ''')
        self.assertEqual(sfz.headers[0]['master_label'], "18x18'' kick")

    def test_version_validator(self):
        sfz = self._parse(
            '''
            <region>
            tune=-400
            ''')
        self.assertEqual(sfz.headers[0]['tune'], -400)

    def test_alias(self):
        sfz = self._parse(
            '''
            <region>
            pitchlfo_depth_oncc17=0.5
            loopmode=loop_sustain
            ''')
        self.assertEqual(sfz.headers[0]['pitchlfo_depth_oncc17'], 0.5)

    def test_double_n(self):
        sfz = self._parse(
            '''
            <region>
            var01_mod=mult
            ''')
        self.assertEqual(sfz.headers[0]['var01_mod'], 'mult')

    def test_target(self):
        sfz = self._parse(
            '''
            <region>
            var01_eq1gain=5
            ''')
        self.assertEqual(sfz.headers[0]['var01_eq1gain'], 5)

    def test_aria_control_code(self):
        sfz = self._parse(
            '''
            <group>amplitude_oncc400=75
            ''')
        self.assertEqual(sfz.headers[0]['amplitude_oncc400'], 75)

    def test_hint(self):
        sfz = self._parse(
            '''
            <control>
            hint_ram_based=1
            set_cc1=0
            label_cc1=gate
            ''')
        self.assertEqual(sfz.headers[0]['hint_ram_based'], 1)

    def test_ucase(self):
        sfz = self._parse(
            '''
            <group>
            Volume=3
            ''')
        self.assertEqual(sfz.headers[0]['volume'], 3)

    def test_ucase_var(self):
        sfz = self._parse(
            '''
            #define $KICKTUNE 40
            <control>
            set_cc$KICKTUNE=63
            ''')
        self.assertEqual(sfz.headers[0]['set_cc40'], 63)

    def test_valid(self):
        sfz = self._parse(
            '''
            <region>
            cutoff_mod=mult amplitude_mod=add
            ''')
        region = sfz.headers[0]
        self.assertEqual(region['cutoff_mod'], 'mult')
