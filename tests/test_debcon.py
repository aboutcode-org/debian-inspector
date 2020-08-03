#
# Copyright (c) nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/debut/

# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from os import path

from commoncode.system import py2
from test_utils import JsonTester  # NOQA

from debut import debcon


class TestGetParagraphData(JsonTester):
    test_data_dir = path.join(path.dirname(__file__), 'data')

    def test_get_paragraph_data_from_file_does_not_crash_on_None(self):
        results = list(debcon.get_paragraph_data_from_file(None))
        assert [] == results

    def test_get_paragraph_data_from_file_from_status(self):
        test_file = self.get_test_loc('debcon/status/one_status')
        expected_loc = 'debcon/status/one_status-expected.json'
        results = debcon.get_paragraph_data_from_file(test_file)
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraph_data_from_file__signed_from_dsc_can_remove_signature(self):
        test_file = self.get_test_loc('debcon/dsc/zlib_1.2.11.dfsg-1.dsc')
        expected_loc = 'debcon/dsc/zlib_1.2.11.dfsg-1.dsc-expected.json'
        results = debcon.get_paragraph_data_from_file(test_file, remove_pgp_signature=True)
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraph_data_from_file__signed_from_dsc_does_not_crash_if_signature_not_removed(self):
        test_file = self.get_test_loc('debcon/dsc/zlib_1.2.11.dfsg-1.dsc')
        expected_loc = 'debcon/dsc/zlib_1.2.11.dfsg-1.dsc-expected-no-desig.json'
        results = debcon.get_paragraph_data_from_file(test_file, remove_pgp_signature=False)
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraph_data_from_file_from_status_can_handle_perl_status(self):
        test_file = self.get_test_loc('debcon/status/perl_status')
        expected_loc = 'debcon/status/perl_status-expected.json'
        results = debcon.get_paragraph_data_from_file(test_file)
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraph_data__invalid_format_returns_none(self):
        text = '''Some text that is not RFC 822
        Compliant'''
        results = debcon.get_paragraph_data(text)
        assert {'unknown': text} == results

    def test_get_paragraph_data_does_not_preserve_keys_case_by_default(self):
        key = 'Some-text'
        value = '''RFC 822
        Compliant'''
        test = '{}: {}'.format(key, value)
        results = debcon.get_paragraph_data(test)
        assert {key.lower(): value} == results

    def test_get_paragraph_data__merge_duplicate_keys(self):
        o1 = 'some: val'
        kv1 = 'key: value1'
        o2 = 'other: val'
        kv2 = 'Key: value2'
        test = '{}\n{}\n{}\n{}'.format(o1, kv1, o2, kv2)
        results = debcon.get_paragraph_data(test)
        expected = [
            ('some', 'val'),
            ('key', 'value1\nvalue2'),
            ('other', 'val')]
        if py2:
            assert sorted(expected) == sorted(results.items())
        else:
            assert expected == list(results.items())

    def test_test_get_paragraph_data__simple(self):
        items = 'A: b\nc: d'
        results = debcon.get_paragraph_data(items)
        expected = {'a': 'b', 'c': 'd'}
        assert expected == results

    def test_test_get_paragraph_data_lowers_only_keys(self):
        items = 'A: B\nDF: D'
        results = debcon.get_paragraph_data(items)
        expected = {'a': 'B', 'df': 'D'}
        assert expected == results

    def test_test_get_paragraph_data_merge_dupes(self):
        items = 'A: B\nDF: D\ndf: x'
        results = debcon.get_paragraph_data(items)
        expected = {'a': 'B', 'df': 'D\nx'}
        assert expected == results

    def test_get_paragraphs_data_from_file__from_copyrights_dep5_1(self):
        test_file = self.get_test_loc('debcon/copyright/dep5-b43-fwcutter.copyright')
        expected_loc = 'debcon/copyright/dep5-b43-fwcutter.copyright-expected.json'
        results = list(debcon.get_paragraphs_data_from_file(test_file))
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraphs_data_from_file__from_copyrights_dep5_3(self):
        test_file = self.get_test_loc('debcon/copyright/dep5-rpm.copyright')
        expected_loc = 'debcon/copyright/dep5-rpm.copyright-expected.json'
        results = list(debcon.get_paragraphs_data_from_file(test_file))
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraphs_data_from_file__from_copyrights_dep5_dropbear(self):
        test_file = self.get_test_loc('debcon/copyright/dropbear.copyright')
        expected_loc = 'debcon/copyright/dropbear.copyright-expected.json'
        results = list(debcon.get_paragraphs_data_from_file(test_file))
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraphs_data_from_file__from_packages(self):
        test_file = self.get_test_loc('debcon/packages/simple_packages')
        expected_loc = 'debcon/packages/simple_packages-expected.json'
        results = list(debcon.get_paragraphs_data_from_file(test_file))
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraphs_data_from_file__from_sources(self):
        test_file = self.get_test_loc('debcon/sources/simple_sources')
        expected_loc = 'debcon/sources/simple_sources-expected.json'
        results = list(debcon.get_paragraphs_data_from_file(test_file))
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraphs_data_from_file__from_status(self):
        test_file = self.get_test_loc('debcon/status/simple_status')
        expected_loc = 'debcon/status/simple_status-expected.json'
        if py2:
            expected_loc = 'debcon/status/simple_status-expected-py2.json'
        results = list(debcon.get_paragraphs_data_from_file(test_file))
        self.check_json(results, expected_loc, sort=py2, regen=False)


class TestDebian822(JsonTester):
    test_data_dir = path.join(path.dirname(__file__), 'data')

    def test_Debian822_from_file__from_status(self):
        test_file = self.get_test_loc('debcon/deb822/one_status')
        expected_loc = 'debcon/deb822/one_status-expected-deb822.json'
        results = debcon.Debian822.from_file(test_file).to_dict()
        self.check_json(results, expected_loc, regen=False)

    def test_Debian822_from_file__signed_from_dsc(self):
        test_file = self.get_test_loc('debcon/deb822/zlib_1.2.11.dfsg-1.dsc')
        expected_loc = 'debcon/deb822/zlib_1.2.11.dfsg-1.dsc-expected-deb822.json'
        results = debcon.Debian822.from_file(test_file).to_dict()
        self.check_json(results, expected_loc, regen=False)

    def test_Debian822_from_items_list(self):
        items = [
            ('Package', 'debut'),
            ('Depends', 'python, python-pip, python-pip-accel'),
            ('Installed-Size', '65'),
        ]
        d822 = debcon.Debian822(items)
        expected = {
            'depends': 'python, python-pip, python-pip-accel',
            'installed-size': '65',
            'package': 'debut',
        }
        assert expected == d822.to_dict()
        expected2 = {
            'depends': 'python, python-pip, python-pip-accel',
            'installed-size': '65',
            'package': 'debut',
        }
        assert expected2 == dict(d822)


class TestDebianFields(JsonTester):
    test_data_dir = path.join(path.dirname(__file__), 'data')

    def test_FormattedTextField(self):
        test = 'simple'
        results = debcon.FormattedTextField.from_value(test)
        assert 'simple' == results.text
        assert 'simple' == results.dumps()

        test = ' simple'
        results = debcon.FormattedTextField.from_value(test)
        assert 'simple' == results.text
        assert 'simple' == results.dumps()

        test = '  simple'
        results = debcon.FormattedTextField.from_value(test)
        assert 'simple' == results.text
        assert 'simple' == results.dumps()

    def test_FormattedTextField_multilines(self):
        test = ''' complex
 some
 .
  nostrip
 .
'''
        results = debcon.FormattedTextField.from_value(test)
        expected = 'complex\nsome\n\n nostrip'
        assert expected == results.text
        expected = 'complex\n some\n .\n  nostrip'
        assert expected == results.dumps()

    def test_DescriptionField(self):
        test = 'simple'
        results = debcon.DescriptionField.from_value(test)
        assert 'simple' == results.synopsis
        assert not results.text
        assert 'simple' == results.dumps()

        test = ' simple'
        assert 'simple' == results.synopsis
        assert not results.text
        assert 'simple' == results.dumps()

        test = '  simple'
        assert 'simple' == results.synopsis
        assert not results.text
        assert 'simple' == results.dumps()

    def test_DescriptionField_multilines(self):
        test = ''' complex
 some
 .
  nostrip
 .
'''
        results = debcon.DescriptionField.from_value(test)
        assert 'complex' == results.synopsis
        assert 'some\n\n nostrip' == results.text
        assert 'complex\n some\n .\n  nostrip' == results.dumps()

    def test_MaintainerField(self):
        test = ' Joe Z. Doe   <me@jzd.me> '
        results = debcon.MaintainerField.from_value(test)
        assert 'Joe Z. Doe' == results.name
        assert 'me@jzd.me' == results.email_address
        assert 'Joe Z. Doe <me@jzd.me>' == results.dumps()

    def test_MaintainerField_incorrect_email(self):
        test = ' Joe Z. Doe   me@j zd.me> '
        results = debcon.MaintainerField.from_value(test)
        assert 'Joe Z. Doe   me@j zd.me>' == results.name
        assert not results.email_address
        assert 'Joe Z. Doe   me@j zd.me>' == results.dumps()

    def test_SingleLineField(self):
        test = ' some value '
        results = debcon.SingleLineField.from_value(test)
        assert 'some value' == results.value
        assert 'some value' == results.dumps()
        assert str(results) == results.dumps()

    def test_LineSeparatedField(self):
        test = ' some value   \n   some value   \n     some more   '
        results = debcon.LineSeparatedField.from_value(test)
        assert ['some value', 'some value', 'some more'] == results.values
        assert 'some value\n some value\n some more' == results.dumps()

    def test_AnyWhiteSpaceSeparatedField(self):
        test = ' some value   \n   some value   \n     some more   '
        results = debcon.AnyWhiteSpaceSeparatedField.from_value(test)
        assert ['some', 'value', 'some', 'value', 'some', 'more'] == results.values
        assert 'some\n value\n some\n value\n some\n more' == results.dumps()

    def test_LineAndSpaceSeparatedField(self):
        test = ' some value \n some value   \n     some more'
        results = debcon.LineAndSpaceSeparatedField.from_value(test)
        assert [('some', 'value'), ('some', 'value'), ('some', 'more')] == results.values
        assert 'some value\n some value\n some more' == results.dumps()
