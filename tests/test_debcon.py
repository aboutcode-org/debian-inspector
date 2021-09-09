#
# Copyright (c) nexB Inc. and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/debian-inspector for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

from os import path

from test_utils import JsonTester  # NOQA

from debian_inspector import debcon


class TestGetParagraphData(JsonTester):
    test_data_dir = path.join(path.dirname(__file__), 'data')

    def test_get_paragraph_data_from_file_does_not_crash_on_None(self):
        results = list(debcon.get_paragraph_data_from_file(None))
        assert results == []

    def test_get_paragraph_data_from_file_from_single_status(self):
        test_file = self.get_test_loc('debcon/status/one_status')
        expected_loc = 'debcon/status/one_status-expected.json'
        results = debcon.get_paragraph_data_from_file(test_file)
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraph_data_from_file_from_status_with_junk_uses_unknown(self):
        test_file = self.get_test_loc('debcon/status/one_status_junk', must_exist=False)
        expected_loc = 'debcon/status/one_status_junk-expected.json'
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
        assert results == {'unknown': text}

    def test_get_paragraph_data_does_not_preserve_keys_case_by_default(self):
        key = 'Some-text'
        value = '''RFC 822
        Compliant'''
        test = '{}: {}'.format(key, value)
        results = debcon.get_paragraph_data(test)
        assert results == {key.lower(): value}

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
        assert list(results.items()) == expected

    def test_test_get_paragraph_data__simple(self):
        items = 'A: b\nc: d'
        results = debcon.get_paragraph_data(items)
        expected = {'a': 'b', 'c': 'd'}
        assert results == expected

    def test_test_get_paragraph_data_lowers_only_keys(self):
        items = 'A: B\nDF: D'
        results = debcon.get_paragraph_data(items)
        expected = {'a': 'B', 'df': 'D'}
        assert results == expected

    def test_test_get_paragraph_data_merge_dupes(self):
        items = 'A: B\nDF: D\ndf: x'
        results = debcon.get_paragraph_data(items)
        expected = {'a': 'B', 'df': 'D\nx'}
        assert results == expected

    def test_get_paragraphs_data__splits_paragraphs_correctly(self):
        test = 'para1: test1\n\npara2: test2'
        results = list(debcon.get_paragraphs_data(test))
        expected = [{'para1': 'test1'}, {'para2': 'test2'}]
        assert results == expected

    def test_split_in_paragraphs__splits_paragraphs_correctly(self):
        test = 'para1: test1\n\npara2: test2'
        results = list(debcon.split_in_paragraphs(test))
        expected = ['para1: test1', 'para2: test2']
        assert results == expected

    def test_split_in_paragraphs__splits_paragraphs_with_multiple_lines_correctly(self):
        test_text_split = """Upstream-Name: GnuPG

Files: *
Copyright: Free Software Foundation, Inc
License: GPL-3+

License: TinySCHEME
 Redistribution


License: permissive
 This file is free software.

License: RFC-Reference
 doc/OpenPGP


License: GPL-3+
 GnuPG
"""

        results = list(debcon.split_in_paragraphs(test_text_split))
        expected = [
            'Upstream-Name: GnuPG',
            'Files: *\nCopyright: Free Software Foundation, Inc\nLicense: GPL-3+',
            'License: TinySCHEME\n Redistribution',
            'License: permissive\n This file is free software.',
            'License: RFC-Reference\n doc/OpenPGP',
            'License: GPL-3+\n GnuPG\n',
        ]
        assert results == expected

    def test_split_in_paragraphs__handles_more_than_two_empty_lines(self):
        test = 'para1: test1\n\n\n\n\npara2: test2'
        results = list(debcon.split_in_paragraphs(test))
        expected = ['para1: test1', 'para2: test2']
        assert results == expected

    def test_split_in_paragraphs__handles_empty_lines_with_spaces(self):
        test = 'para1: test1\n\n \t     \n          \npara2: test2'
        results = list(debcon.split_in_paragraphs(test))
        expected = ['para1: test1', 'para2: test2']
        assert results == expected

    def test_get_paragraphs_data_from_text__from_status_file(self):
        test_file = self.get_test_loc('debcon/status/simple_status')
        with open(test_file) as tf:
            test_file = tf.read()
        expected_loc = 'debcon/status/simple_status-expected.json'
        results = list(debcon.get_paragraphs_data(test_file))
        self.check_json(results, expected_loc, regen=False)

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
        results = list(debcon.get_paragraphs_data_from_file(test_file))
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraph_data__return_unknow_if_we_have_payload(self):
        # we were skipping email payloads: a payload means this is not a
        # header only file and therefore something we cannot process normally
        test = 'Foo: home\n\nBar: baz'
        results = debcon.get_paragraph_data(test)
        expected = {'foo': 'home', 'unknown': 'Bar: baz'}
        assert results == expected


class TestDebian822(JsonTester):
    test_data_dir = path.join(path.dirname(__file__), 'data')

    def test_Debian822_from_file__from_one_status(self):
        test_file = self.get_test_loc('debcon/deb822/one_status')
        expected_loc = 'debcon/deb822/one_status-expected-deb822.json'
        results = debcon.Debian822.from_file(test_file).to_dict()
        self.check_json(results, expected_loc, regen=False)

    def test_Debian822_from_file__from_one_status_keeps_unknown_junk(self):
        test_file = self.get_test_loc('debcon/deb822/one_status_junk')
        expected_loc = 'debcon/deb822/one_status_junk-expected-deb822.json'
        results = debcon.Debian822.from_file(test_file).to_dict()
        self.check_json(results, expected_loc, regen=False)

    def test_Debian822_from_string__from_one_status(self):
        test_file = self.get_test_loc('debcon/deb822/one_status')
        with open(test_file) as tf:
            test_file = tf.read()
        expected_loc = 'debcon/deb822/one_status-expected-deb822.json'
        results = debcon.Debian822.from_string(test_file).to_dict()
        self.check_json(results, expected_loc, regen=False)

    def test_Debian822_from_file__signed_from_dsc(self):
        test_file = self.get_test_loc('debcon/deb822/zlib_1.2.11.dfsg-1.dsc')
        expected_loc = 'debcon/deb822/zlib_1.2.11.dfsg-1.dsc-expected-deb822.json'
        results = debcon.Debian822.from_file(test_file).to_dict()
        self.check_json(results, expected_loc, regen=False)

    def test_Debian822_from_items_list(self):
        items = [
            ('Package', 'debian_inspector'),
            ('Depends', 'python, python-pip, python-pip-accel'),
            ('Installed-Size', '65'),
        ]
        d822 = debcon.Debian822(items)
        expected = {
            'depends': 'python, python-pip, python-pip-accel',
            'installed-size': '65',
            'package': 'debian_inspector',
        }
        assert d822.to_dict() == expected
        expected2 = {
            'depends': 'python, python-pip, python-pip-accel',
            'installed-size': '65',
            'package': 'debian_inspector',
        }
        assert dict(d822) == expected2


class TestDebianFields(JsonTester):
    test_data_dir = path.join(path.dirname(__file__), 'data')

    def test_FormattedTextField(self):
        test = 'simple'
        results = debcon.FormattedTextField.from_value(test)
        assert results.text == 'simple'
        assert results.dumps() == 'simple'

        test = ' simple'
        results = debcon.FormattedTextField.from_value(test)
        assert results.text == 'simple'
        assert results.dumps() == 'simple'

        test = '  simple'
        results = debcon.FormattedTextField.from_value(test)
        assert results.text == 'simple'
        assert results.dumps() == 'simple'

    def test_FormattedTextField_multilines(self):
        test = ''' complex
 some
 .
  nostrip
 .
'''
        results = debcon.FormattedTextField.from_value(test)
        expected = 'complex\nsome\n\n nostrip\n'
        assert results.text == expected
        expected = 'complex\n some\n .\n  nostrip'
        assert results.dumps() == expected

    def test_DescriptionField(self):
        test = 'simple'
        results = debcon.DescriptionField.from_value(test)
        assert results.synopsis == 'simple'
        assert not results.text
        assert results.dumps() == 'simple'

        test = ' simple'
        assert results.synopsis == 'simple'
        assert not results.text
        assert results.dumps() == 'simple'

        test = '  simple'
        assert results.synopsis == 'simple'
        assert not results.text
        assert results.dumps() == 'simple'

    def test_DescriptionField_multilines(self):
        test = ''' complex
 some
 .
  nostrip
 .
'''
        results = debcon.DescriptionField.from_value(test)
        assert results.synopsis == 'complex'
        assert results.text == 'some\n\n nostrip\n'
        assert results.dumps() == 'complex\n some\n .\n  nostrip'

    def test_MaintainerField(self):
        test = ' Joe Z. Doe   <me@jzd.me> '
        results = debcon.MaintainerField.from_value(test)
        assert results.name == 'Joe Z. Doe'
        assert results.email_address == 'me@jzd.me'
        assert results.dumps() == 'Joe Z. Doe <me@jzd.me>'

    def test_MaintainerField_incorrect_email(self):
        test = ' Joe Z. Doe   me@j zd.me> '
        results = debcon.MaintainerField.from_value(test)
        assert results.name == 'Joe Z. Doe   me@j zd.me>'
        assert not results.email_address
        assert results.dumps() == 'Joe Z. Doe   me@j zd.me>'

    def test_SingleLineField(self):
        test = ' some value '
        results = debcon.SingleLineField.from_value(test)
        assert results.value == 'some value'
        assert results.dumps() == 'some value'
        assert results.dumps() == str(results)

    def test_LineSeparatedField(self):
        test = ' some value   \n   some value   \n     some more   '
        results = debcon.LineSeparatedField.from_value(test)
        assert results.values == ['some value', 'some value', 'some more']
        assert results.dumps() == 'some value\n some value\n some more'

    def test_AnyWhiteSpaceSeparatedField(self):
        test = ' some value   \n   some value   \n     some more   '
        results = debcon.AnyWhiteSpaceSeparatedField.from_value(test)
        assert results.values == ['some', 'value', 'some', 'value', 'some', 'more']
        assert results.dumps() == 'some\n value\n some\n value\n some\n more'

    def test_LineAndSpaceSeparatedField(self):
        test = ' some value \n some value   \n     some more'
        results = debcon.LineAndSpaceSeparatedField.from_value(test)
        assert results.values == [('some', 'value'), ('some', 'value'), ('some', 'more')]
        assert results.dumps() == 'some value\n some value\n some more'
