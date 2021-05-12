#
# Copyright (c) nexB Inc. and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# SPDX-License-Identifier: MIT
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/debian-inspector for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
# Author: Peter Odding <peter@peterodding.com>
# Last Change: March 9, 2021
# URL: https://github.com/xolox/python-deb-pkg-tools


from unittest import TestCase

from debian_inspector.version import Version


class DebPkgToolsTestCase(TestCase):

    def test_version_sorting(self):
        # Check version sorting implemented on top of `=' and `<<' comparisons.
        expected_order = ['0.1', '0.5', '1.0', '2.0', '3.0', '1:0.4', '2:0.3']
        assert list(sorted(expected_order)) != expected_order
        result = [str(v) for v in sorted(map(Version.from_string, expected_order))]
        assert expected_order == result

    def test_version_comparison(self):
        assert Version.from_string('1.0') > Version.from_string('0.5')
        assert Version.from_string('1:0.5') > Version.from_string('2.0')
        assert not Version.from_string('0.5') > Version.from_string('2.0')

        assert Version.from_string('0.75') >= Version.from_string('0.5')
        assert Version.from_string('0.50') >= Version.from_string('0.5')
        assert Version.from_string('1:0.5') >= Version.from_string('5.0')
        assert not Version.from_string('0.2') >= Version.from_string('0.5')

        assert Version.from_string('0.5') < Version.from_string('1.0')
        assert Version.from_string('2.0') < Version.from_string('1:0.5')
        assert not Version.from_string('2.0') < Version.from_string('0.5')

        assert Version.from_string('0.5') <= Version.from_string('0.75')
        assert Version.from_string('0.5') <= Version.from_string('0.50')
        assert Version.from_string('5.0') <= Version.from_string('1:0.5')
        assert not Version.from_string('0.5') <= Version.from_string('0.2')

        assert Version.from_string('42') == Version.from_string('42')
        assert Version.from_string('0.5') == Version.from_string('0:0.5')
        assert Version.from_string('0.5') != Version.from_string('1.0')

        assert Version.from_string('1') != Version.from_string('0')
        assert not Version.from_string('0.5') != Version.from_string('0:0.5')

        assert Version.from_string("1.3~rc2") < Version.from_string("1.3")
