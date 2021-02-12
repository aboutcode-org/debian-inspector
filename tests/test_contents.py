#
# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debut/

# SPDX-License-Identifier: Apache-2.0

from os import path

from test_utils import JsonTester  # NOQA

from debut import contents


class TestContentsParse(JsonTester):
    test_data_dir = path.join(path.dirname(__file__), 'data')

    def test_parse_contents_ubuntu_with_header_plain(self):
        test_file = self.get_test_loc('contents/ubuntu_Contents-i386')
        expected_loc = 'contents/ubuntu_Contents-i386-expected.json'
        results = contents.parse_contents(test_file, has_header=True)
        self.check_json(results, expected_loc, regen=False)

    def test_parse_contents_debian_no_header_gzipped(self):
        test_file = self.get_test_loc('contents/debian_Contents-amd64.gz')
        expected_loc = 'contents/debian_Contents-amd64.gz-expected.json'
        results = contents.parse_contents(test_file, has_header=False)
        self.check_json(results, expected_loc, regen=False)

    def test_parse_contents_debian_is_same_gzipped_or_not(self):
        test_file = self.get_test_loc('contents/debian_Contents-amd64.gz')
        results = contents.parse_contents(test_file, has_header=False)

        test_file2 = self.get_test_loc('contents/debian_Contents-amd64')
        results2 = contents.parse_contents(test_file2, has_header=False)

        assert results == results2
