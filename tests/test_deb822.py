#
# Copyright (c) nexB Inc. and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/debian-inspector for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

from os import path

from test_utils import JsonTester  # NOQA

from debian_inspector import deb822
from debian_inspector.deb822 import HeaderField
from debian_inspector.deb822 import NumberedLine


def get_paras_data(test_file):
    return [
        [h.to_dict() for h in p]
        for p in deb822.get_header_fields_groups_from_file(test_file)
    ]


class TestGetParagraphsData(JsonTester):
    test_data_dir = path.join(path.dirname(__file__), 'data')

    def test_get_paragraphs_data__splits_paragraphs_with_multiple_lines_correctly(self):
        test = """Upstream-Name: GnuPG

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
  . formatted  
   also formatted 
"""
        results = list(deb822.get_header_fields_groups(test))
        expected = [
            [HeaderField(lines=[NumberedLine(number=1, value='GnuPG')], name='upstream-name')],
            [
                HeaderField(lines=[NumberedLine(number=3, value='*')], name='files'),
                HeaderField(lines=[NumberedLine(number=4, value='Free Software Foundation, Inc')], name='copyright'),
                HeaderField(lines=[NumberedLine(number=5, value='GPL-3+')], name='license')
            ],
            [HeaderField(lines=[
                NumberedLine(number=7, value='TinySCHEME'),
                NumberedLine(number=8, value=' Redistribution')
            ], name='license')],
            [HeaderField(lines=[
                NumberedLine(number=11, value='permissive'),
                NumberedLine(number=12, value=' This file is free software.')
            ], name='license')],
            [HeaderField(lines=[
                NumberedLine(number=14, value='RFC-Reference'),
                NumberedLine(number=15, value=' doc/OpenPGP')
            ], name='license')],
            [HeaderField(name='license', lines=[
                NumberedLine(number=18, value='GPL-3+'), 
                NumberedLine(number=19, value=' GnuPG'), 
                NumberedLine(number=20, value='  . formatted'), 
                NumberedLine(number=21, value='   also formatted')
            ])],
        ]

        assert results == expected

    def test_get_paragraphs_data__splits_paragraphs_correctly(self):
        test = 'para1: test1\n\npara2: test2'
        results = list(deb822.get_header_fields_groups(test))
        expected = [
            [HeaderField(lines=[NumberedLine(number=1, value='test1')], name='para1')],
            [HeaderField(lines=[NumberedLine(number=3, value='test2')], name='para2')],
        ]
        assert results == expected

    def test_get_paragraphs_data__handles_more_than_two_empty_lines(self):
        test = 'para1: test1\n\n\n\n\npara2: test2\n test3'
        results = list(deb822.get_header_fields_groups(test))
        expected = [
            [HeaderField(name='para1', lines=[NumberedLine(number=1, value='test1')])],
            [HeaderField(name='para2', lines=[
                NumberedLine(number=6, value='test2'),
                NumberedLine(number=7, value=' test3')
            ])],
        ]
        assert results == expected

    def test_get_paragraphs_data__handles_empty_lines_with_spaces(self):
        test = '\n\npara1: test1\n\n \t     \n          \npara2: test2'
        results = list(deb822.get_header_fields_groups(test))
        expected = [
            [HeaderField(name='para1', lines=[NumberedLine(number=3, value='test1')])],
            [HeaderField(name='para2', lines=[NumberedLine(number=7, value='test2')])],
        ]
        assert results == expected

    def test_get_paragraphs_data_from_file__from_copyrights_dep5_1(self):
        test_file = self.get_test_loc('deb822/dep5-b43-fwcutter.copyright')
        expected_loc = 'deb822/dep5-b43-fwcutter.copyright-expected.json'
        results = get_paras_data(test_file)
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraphs_data_from_file__from_copyrights_dep5_3(self):
        test_file = self.get_test_loc('deb822/dep5-rpm.copyright')
        expected_loc = 'deb822/dep5-rpm.copyright-expected.json'
        results = get_paras_data(test_file)
        self.check_json(results, expected_loc, regen=False)

    def test_get_paragraphs_data_from_file__from_copyrights_dep5_dropbear(self):
        test_file = self.get_test_loc('deb822/dropbear.copyright')
        expected_loc = 'deb822/dropbear.copyright-expected.json'
        results = get_paras_data(test_file)
        self.check_json(results, expected_loc, regen=False)
