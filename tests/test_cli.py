# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import patch
from pathlib import Path
from collections import namedtuple
from sfzlint import lint


fixture_dir = Path(__file__).parent / 'fixtures'


class ErrMsg(namedtuple('errmsg', (
        'file', 'row', 'column', 'level', 'message'))):
    def __new__(cls, file, row, column, l_m):
        level, message = l_m.split(' ', 1)
        return super().__new__(cls, file, row, column, level, message)


class TestCLI(TestCase):
    def assert_has_message(self, message, err_list):
        msglen = len(message)
        msgs = {e.message[:msglen] for e in err_list}
        self.assertIn(message, msgs)

    @patch('sys.argv', new=[
        'sfzlint', str(fixture_dir / 'basic/valid.sfz')])
    @patch('builtins.print')
    def test_valid_file(self, print_mock):
        lint.main()
        self.assertFalse(print_mock.called, print_mock.call_args_list)

    @patch('sys.argv', new=[
        'sfzlint', str(fixture_dir / 'basic/bad.sfz')])
    @patch('builtins.print')
    def test_invalid_file(self, print_mock):
        lint.main()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        self.assert_has_message('unknown opcode', calls)

    @patch('sys.argv', new=[
        'sfzlint', str(fixture_dir / 'basic')])
    def test_lint_dir(self):
        with patch('builtins.print') as print_mock:
            lint.main()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        self.assert_has_message('unknown opcode', calls)

    @patch('sys.argv', new=[
        'sfzlint', str(fixture_dir / 'include/hasinc.sfz')])
    @patch('builtins.print')
    def test_include_define(self, print_mock):
        lint.main()
        self.assertFalse(print_mock.called, print_mock.call_args_list)

    @patch('sys.argv', new=[
        'sfzlint', str(fixture_dir / 'basic/valid.sfz'),
        '--spec-version', 'v1'])
    @patch('builtins.print')
    def test_spec_version(self, print_mock):
        lint.main()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        self.assert_has_message('header spec v2 not in', calls)
        self.assert_has_message('opcode spec aria is not', calls)

    @patch('sys.argv', new=[
        'sfzlint', str(fixture_dir / 'basic/nosample.sfz')])
    @patch('builtins.print')
    def test_missing_sample(self, print_mock):
        lint.main()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        self.assert_has_message('file not found', calls)

    @patch('sys.argv', new=[
        'sfzlint', str(fixture_dir / 'basic/badcase.sfz')])
    def test_bad_case(self):
        with patch('builtins.print') as print_mock:
            lint.main()
        self.assertTrue(print_mock.called)
        calls = [ErrMsg(*a[0][0].split(':'))
                 for a in print_mock.call_args_list]
        self.assert_has_message('case does not match', calls)
