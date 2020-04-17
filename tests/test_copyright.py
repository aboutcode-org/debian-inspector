#
# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debut/

# SPDX-License-Identifier: Apache-2.0


from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from os import path

from commoncode.system import py2
from test_utils import JsonTester  # NOQA

from debut import copyright


class TestCopyrightFields(JsonTester):
    test_data_dir = path.join(path.dirname(__file__), 'data')

    def test_CopyrightStatementField(self):
        test = ' 2012-12  MyCom  inc. '
        results = copyright.CopyrightStatementField.from_value(test)
        assert '2012-12' == results.year_range
        assert 'MyCom inc.' == results.holder
        assert '2012-12 MyCom inc.' == results.dumps()

    def test_CopyrightStatementField_no_year(self):
        test = '   MyCom  inc. '
        results = copyright.CopyrightStatementField.from_value(test)
        assert 'MyCom inc.' == results.holder
        assert not results.year_range
        assert 'MyCom inc.' == results.dumps()

    def test_is_year_range(self):
        assert copyright.is_year_range('2012')
        assert copyright.is_year_range('2012-1999')
        assert not copyright.is_year_range('2012-now')
        assert not copyright.is_year_range(' MyCom ')
        assert not copyright.is_year_range(' ')
        assert not copyright.is_year_range('')
        assert not copyright.is_year_range(None)

    def test_LicenseField(self):
        test = '  sim ple   '
        results = copyright.LicenseField.from_value(test)
        assert 'sim ple' == results.name
        assert not results.text
        assert 'sim ple' == results.dumps()

    def test_LicenseField_with_text(self):
        test = ''' GPL 2.0
 licensed under the gpl
 .
  attribution
 .
'''
        results = copyright.LicenseField.from_value(test)
        assert 'GPL 2.0' == results.name
        assert 'licensed under the gpl\n\n attribution' == results.text
        assert 'GPL 2.0\n licensed under the gpl\n .\n  attribution' == results.dumps()


class TestDebianCopyright(JsonTester):
    test_data_dir = path.join(path.dirname(__file__), 'data')

    def test_DebianCopyright_from_file__from_copyrights_dep5_1(self):
        test_file = self.get_test_loc('copyright/dep5-b43-fwcutter.copyright')
        expected_loc = 'copyright/dep5-b43-fwcutter.copyright-expected-DebianCopyright.json'
        results = copyright.DebianCopyright.from_file(test_file)
        self.check_json(results.to_dict(), expected_loc, regen=False)

    def test_DebianCopyright_from_file__from_copyrights_dep5_3(self):
        test_file = self.get_test_loc('copyright/dep5-rpm.copyright')
        expected_loc = 'copyright/dep5-rpm.copyright-expected-DebianCopyright.json'
        results = copyright.DebianCopyright.from_file(test_file)
        self.check_json(results.to_dict(), expected_loc, regen=False)

    def test_DebianCopyright_from_file__from_copyrights_dep5_dropbear(self):
        test_file = self.get_test_loc('copyright/dropbear.copyright')
        expected_loc = 'copyright/dropbear.copyright-expected-DebianCopyright.json'
        results = copyright.DebianCopyright.from_file(test_file)
        self.check_json(results.to_dict(), expected_loc, regen=False)

    def test_DebianCopyright_from_file__from_copyrights_dep5_1_dumps(self):
        test_file = self.get_test_loc('copyright/dep5-b43-fwcutter.copyright')
        expected_loc = 'copyright/dep5-b43-fwcutter.copyright-expected.dumps'
        results = copyright.DebianCopyright.from_file(test_file).dumps()
        self.check_file(results, expected_loc, sort=py2, regen=False)

    def test_DebianCopyright_from_file__from_copyrights_dep5_3_dumps(self):
        test_file = self.get_test_loc('copyright/dep5-rpm.copyright')
        expected_loc = 'copyright/dep5-rpm.copyright-expected.dumps'
        results = copyright.DebianCopyright.from_file(test_file).dumps()
        self.check_file(results, expected_loc, sort=py2, regen=False)

    def test_DebianCopyright_from_file__from_copyrights_dep5_dropbear_dumps(self):
        test_file = self.get_test_loc('copyright/dropbear.copyright')
        expected_loc = 'copyright/dropbear.copyright-expected.dumps'
        results = copyright.DebianCopyright.from_file(test_file).dumps()
        self.check_file(results, expected_loc, sort=py2, regen=False)
