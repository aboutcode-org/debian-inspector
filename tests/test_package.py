# Debian packaging tools: Automated tests.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 12, 2019
# URL: https://github.com/xolox/python-deb-pkg-tools
# Copyright (c) 2018 Peter Odding
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from os import path
import re

import unittest

from debut import version
from debut import control
from debut import debcon
from debut import deps
from debut import package


class PackageTestCase(unittest.TestCase):

    def test_find_latest_version(self):
        good = ['name_1.0_all.deb', 'name_0.5_all.deb']
        assert path.basename(package.find_latest_version(good).original_filename) == 'name_1.0_all.deb'
        bad = ['one_1.0_all.deb', 'two_0.5_all.deb']
        self.assertRaises(ValueError, package.find_latest_version, bad)

    def test_find_latest_versions(self):
        packages = ['one_1.0_all.deb', 'one_0.5_all.deb', 'two_1.5_all.deb', 'two_0.1_all.deb']
        results = sorted(
            [path.basename(a.original_filename)
             for a in package.find_latest_versions(packages).values()])
        assert sorted(['one_1.0_all.deb', 'two_1.5_all.deb']) == results

    def test_test_DebArch_from_filename(self):
        filename = '/var/cache/apt/archives/python2.7_2.7.3-0ubuntu3.4_amd64.deb'
        deb = package.DebArchive.from_filename(filename)
        assert 'python2.7' == deb.name
        assert '2.7.3-0ubuntu3.4' == str(deb.version)
        assert 'amd64' == deb.architecture
        assert filename == deb.original_filename

    def test_DebArch_from_filename__raise_ValueError_on_errors(self):
        self.assertRaises(ValueError, package.DebArchive.from_filename, 'python2.7_2.7.3-0ubuntu3.4_amd64.not-a-deb')
        self.assertRaises(ValueError, package.DebArchive.from_filename, 'python2.7.deb')


V = version.Version.from_string

class VersionTestCase(unittest.TestCase):
    # Check each individual operator (to make sure the two implementations
    # agree). We use the Version() class for this so that we test both
    # compare_versions() and the Version() wrapper.

    def test_version_comparison_can_sort(self):
        # Check version sorting implemented on top of `=' and `<<' comparisons.
        expected_order = ['0.1', '0.5', '1.0', '2.0', '3.0', '1:0.4', '2:0.3']
        assert expected_order != list(sorted(expected_order))
        assert expected_order == list(map(str, sorted(map(V, expected_order))))

    def test_version_comparison_superior(self):
        assert V('1.0') > V('0.5')  # usual semantics
        assert V('1:0.5') > V('2.0')  # unusual semantics
        assert not V('0.5') > V('2.0')  # sanity check

    def test_version_comparison_superior_or_equal(self):
        assert V('0.75') >= V('0.5')  # usual semantics
        assert V('0.50') >= V('0.5')  # usual semantics
        assert V('1:0.5') >= V('5.0')  # unusual semantics
        assert not V('0.2') >= V('0.5')  # sanity check

    def test_version_comparison_inferior(self):
        assert V('0.5') < V('1.0')  # usual semantics
        assert V('2.0') < V('1:0.5')  # unusual semantics
        assert not V('2.0') < V('0.5')  # sanity check

    def test_version_comparison_inferior_or_equal(self):
        assert V('0.5') <= V('0.75')  # usual semantics
        assert V('0.5') <= V('0.50')  # usual semantics
        assert V('5.0') <= V('1:0.5')  # unusual semantics
        assert not V('0.5') <= V('0.2')  # sanity check

    def test_version_comparison_equal(self):
        assert V('42') == V('42')  # usual semantics
        assert V('0.5') == V('0:0.5')  # unusual semantics
        assert not V('0.5') == V('1.0')  # sanity check

    def test_version_comparison_not_equal(self):
        assert V('1') != V('0')  # usual semantics
        assert not V('0.5') != V('0:0.5')  # unusual semantics


class ControlTestCase(unittest.TestCase):

    def test_control_field_parsing(self):
        """Test the parsing of control file fields."""
        deb822_package = debcon.Debian822([
            ('Package', 'python-py2deb'),
            ('Depends', 'python-deb-pkg-tools, python-pip, python-pip-accel'),
            ('Installed-Size', '42'),
        ])
        parsed_info = control.parse_control_fields(deb822_package)
        expected = {
            'Package': 'python-py2deb',
            'Depends': deps.AndRelationships((
                deps.Relationship(name=u'python-deb-pkg-tools'),
                deps.Relationship(name=u'python-pip'),
                deps.Relationship(name=u'python-pip-accel')
                )),
            'Installed-Size': 42
        }
        assert expected == parsed_info

