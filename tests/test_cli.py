# -*- coding: utf-8 -*-

import os
from unittest import TestCase
from unittest.mock import patch, MagicMock
from pathlib import Path
from collections import namedtuple
from sfzlint.cli import sfzlint, sfzlist
from sfzlint import settings


fixture_dir = Path(__file__).parent / 'fixtures'
is_fs_case_insensitive = (
    os.path.exists(__file__.upper()) and os.path.exists(__file__.lower()))


class ErrMsg(namedtuple('errmsg', (
        'file', 'row', 'column', 'level', 'message'))):
    def __new__(cls, file, row, column, l_m):
        level, message = l_m.split(' ', 1)
        return super().__new__(cls, file, row, column, level, message)


def patchargs(path, *args):
    newargv = ['sfzlint', '--no-pickle', str(fixture_dir / path)] + list(args)

    def wrapper(fn):
        return patch('sys.argv', new=newargv)(fn)

    return wrapper


class TestSFZLint(TestCase):
    def tearDown(self):
        # Ensure this does not get accidentally set
        self.assertFalse(settings.pickle)

    def assert_has_message(self, message, err_list):
        msglen = len(message)
        msgs = {e.message[:msglen] for e in err_list}
        self.assertIn(message, msgs, f'{message} not in {err_list}')

    @patchargs('basic/valid.sfz')
    @patch('builtins.print')
    def test_valid_file(self, print_mock):
        sfzlint()
        self.assertFalse(print_mock.called, print_mock.call_args_list)

    @patchargs('basic/bad.sfz')
    @patch('builtins.print')
    def test_invalid_file(self, print_mock):
        sfzlint()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        self.assert_has_message('unknown opcode', calls)

    @patchargs('basic')
    def test_lint_dir(self):
        with patch('builtins.print') as print_mock:
            sfzlint()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        self.assert_has_message('unknown opcode', calls)

    @patchargs('include/inbadfile.sfz')
    def test_include_parse_error(self):
        with patch('builtins.print') as print_mock:
            sfzlint()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':', 3))
                 for a in print_mock.call_args_list]
        self.assert_has_message('error loading include', calls)

    @patchargs('include/hasinc.sfz')
    @patch('builtins.print')
    def test_include_define(self, print_mock):
        sfzlint()
        self.assertFalse(print_mock.called, print_mock.call_args_list)

    @patchargs('basic/valid.sfz', '--spec-version', 'v1')
    @patch('builtins.print')
    def test_spec_version(self, print_mock):
        sfzlint()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        self.assert_has_message('header spec v2 not in', calls)
        self.assert_has_message('opcode spec v2 is not', calls)

    @patchargs('basic/nosample.sfz')
    @patch('builtins.print')
    def test_missing_sample(self, print_mock):
        sfzlint()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        self.assert_has_message('file not found', calls)

    @patchargs('basic/relsample.sfz')
    def test_relative_path(self):
        with patch('builtins.print') as print_mock:
            sfzlint()
        self.assertFalse(print_mock.called, print_mock.call_args_list)

    @patchargs('basic/def_path.sfz')
    def test_default_path(self):
        with patch('builtins.print') as print_mock:
            sfzlint()
        self.assertFalse(print_mock.called, print_mock.call_args_list)

    @patchargs('basic/badcase.sfz')
    def test_bad_case(self):
        with patch('builtins.print') as print_mock:
            sfzlint()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        if (is_fs_case_insensitive):
            self.assert_has_message('case does not match', calls)
        else:
            self.assert_has_message('file not found', calls)

    @patchargs('include/sub/relpath.sfz',
               '--rel-path', str(fixture_dir / 'include'))
    def test_rel_path(self):
        with patch('builtins.print') as print_mock:
            sfzlint()
        self.assertFalse(print_mock.called, print_mock.call_args_list)

    @patchargs('aria_program.xml')
    def test_xml_with_defines(self):
        with patch('builtins.print') as print_mock:
            sfzlint()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        self.assertEqual(1, len(calls), calls)
        self.assertIn('foo', calls[0].message)


class TestSFZList(TestCase):
    @patch('sys.argv', new=['sfzlist', '--no-pickle'])
    def test_valid_file(self):
        print_mock = MagicMock()
        sfzlist(print_mock)
        self.assertTrue(print_mock.called)
        opcodes = {line[0][0].split(' ', 1)[0]
                   for line in print_mock.call_args_list}
        for test_opcode in ('cutoff2_onccN', 'sample', '*_mod', 'curve_index'):
            self.assertIn(test_opcode, opcodes)

    @patch('sys.argv', new=[
        'sfzlist', '--no-pickle', '--path', str(fixture_dir / 'basic')])
    def test_path_dir(self):
        print_mock = MagicMock()
        sfzlist(print_mock)
        self.assertTrue(print_mock.called)
        opcodes = {line[0][0].split(' ', 1)[0]
                   for line in print_mock.call_args_list}
        for test_opcode in ('foo', 'sw_default', 'amp_velcurve_N'):
            self.assertIn(test_opcode, opcodes)
        for test_opcode in ('cutoff2_onccN', 'curve_index', '*_mod'):
            self.assertNotIn(test_opcode, opcodes)

    @patch('sys.argv', new=[
        'sfzlist', '--no-pickle', '--path', str(fixture_dir / 'basic/valid.sfz')])
    def test_path_dir(self):
        print_mock = MagicMock()
        sfzlist(print_mock)
        self.assertTrue(print_mock.called)
        opcodes = {line[0][0].split(' ', 1)[0]
                   for line in print_mock.call_args_list}
        for test_opcode in ('sw_default', 'amp_velcurve_N'):
            self.assertIn(test_opcode, opcodes)
        for test_opcode in ('cutoff2_onccN', 'curve_index', '*_mod'):
            self.assertNotIn(test_opcode, opcodes)
