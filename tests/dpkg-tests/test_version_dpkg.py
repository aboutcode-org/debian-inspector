#!/usr/bin/python

# SPDX-License-Identifier: GPL-2.0-or-later
#

# libdpkg - Debian packaging suite library routines
# t-version.c - test version handling
#
# Copyright © 2009-2014 Guillem Jover <guillem@debian.org>
#
# This is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 2 of the License, or
# (at your option) any later version.
#
# This is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from unittest import TestCase

from debian_inspector import version
from unittest.case import expectedFailure

DPKG_VERSION_OBJECT = version.Version
dpkg_version_compare = version.compare_versions
dpkg_version_relate = version.eval_constraint
parseversion = version.Version.from_string


class VersionTests(TestCase):

    def test_version_compare(self):
        a = DPKG_VERSION_OBJECT(0, "1", "1")
        b = DPKG_VERSION_OBJECT(0, "2", "1")
        assert not dpkg_version_compare(a, b) == 0

        a = DPKG_VERSION_OBJECT(0, "1", "1")
        b = DPKG_VERSION_OBJECT(0, "1", "2")
        assert not dpkg_version_compare(a, b) == 0

        #  Test for version equality.
        a = b = DPKG_VERSION_OBJECT(0, "0", "0")
        assert dpkg_version_compare(a, b) == 0

        a = DPKG_VERSION_OBJECT(0, "0", "00")
        b = DPKG_VERSION_OBJECT(0, "00", "0")
        assert dpkg_version_compare(a, b) == 0

        a = b = DPKG_VERSION_OBJECT(1, "2", "3")
        assert dpkg_version_compare(a, b) == 0

        #  Test for epoch difference.
        a = DPKG_VERSION_OBJECT(0, "0", "0")
        b = DPKG_VERSION_OBJECT(1, "0", "0")
        assert dpkg_version_compare(a, b) < 0
        assert dpkg_version_compare(b, a) > 0

        #  Test for version component difference.
        a = DPKG_VERSION_OBJECT(0, "a", "0")
        b = DPKG_VERSION_OBJECT(0, "b", "0")
        assert dpkg_version_compare(a, b) < 0
        assert dpkg_version_compare(b, a) > 0

        #  Test for revision component difference.
        a = DPKG_VERSION_OBJECT(0, "0", "a")
        b = DPKG_VERSION_OBJECT(0, "0", "b")
        assert dpkg_version_compare(a, b) < 0
        assert dpkg_version_compare(b, a) > 0

        #  FIXME: Complete.

    def test_version_relate(self):

        a = DPKG_VERSION_OBJECT(0, "1", "1")
        b = DPKG_VERSION_OBJECT(0, "1", "1")
        assert dpkg_version_relate(a, '=', b)
        assert not dpkg_version_relate(a, '<<', b)
        assert dpkg_version_relate(a, '<=', b)
        assert not dpkg_version_relate(a, '>>', b)
        assert dpkg_version_relate(a, '>=', b)

        a = DPKG_VERSION_OBJECT(0, "1", "1")
        b = DPKG_VERSION_OBJECT(0, "2", "1")
        assert not dpkg_version_relate(a, '=', b)
        assert dpkg_version_relate(a, '<<', b)
        assert dpkg_version_relate(a, '<=', b)
        assert not dpkg_version_relate(a, '>>', b)
        assert not dpkg_version_relate(a, '>=', b)

        a = DPKG_VERSION_OBJECT(0, "2", "1")
        b = DPKG_VERSION_OBJECT(0, "1", "1")
        assert not dpkg_version_relate(a, '=', b)
        assert not dpkg_version_relate(a, '<<', b)
        assert not dpkg_version_relate(a, '<=', b)
        assert dpkg_version_relate(a, '>>', b)
        assert dpkg_version_relate(a, '>=', b)

    def test_version_parse(self):
        b = DPKG_VERSION_OBJECT(0, "0", "")

        a = parseversion("0")
        assert dpkg_version_compare(a, b) == 0

        a = parseversion("0:0")
        assert dpkg_version_compare(a, b) == 0

        b = DPKG_VERSION_OBJECT(0, "0", "0")
        a = parseversion("0:0-0")
        assert dpkg_version_compare(a, b) == 0

        b = DPKG_VERSION_OBJECT(0, "0.0", "0.0")
        a = parseversion("0:0.0-0.0")
        assert dpkg_version_compare(a, b) == 0

        #  Test epoched versions.
        b = DPKG_VERSION_OBJECT(1, "0", "")
        a = parseversion("1:0")
        assert dpkg_version_compare(a, b) == 0

        b = DPKG_VERSION_OBJECT(5, "1", "")
        a = parseversion("5:1")
        assert dpkg_version_compare(a, b) == 0

        #  Test multiple hyphens.
        b = DPKG_VERSION_OBJECT(0, "0-0", "0")
        a = parseversion("0:0-0-0")
        assert dpkg_version_compare(a, b) == 0

        b = DPKG_VERSION_OBJECT(0, "0-0-0", "0")
        a = parseversion("0:0-0-0-0")
        assert dpkg_version_compare(a, b) == 0

    @expectedFailure
    def test_version_parse_fails_with_multiple_colons_while_dpkg_pass1(self):
        #  Test multiple colons.
        b = DPKG_VERSION_OBJECT(0, "0:0", "0")
        a = parseversion("0:0:0-0")
        assert dpkg_version_compare(a, b) == 0

    @expectedFailure
    def test_version_parse_fails_with_multiple_colons_while_dpkg_pass2(self):
        b = DPKG_VERSION_OBJECT(0, "0:0:0", "0")
        a = parseversion("0:0:0:0-0")
        assert dpkg_version_compare(a, b) == 0

    @expectedFailure
    def test_version_parse_fails_with_multiple_colons_while_dpkg_pass3(self):
        #  Test multiple hyphens and colons.
        b = DPKG_VERSION_OBJECT(0, "0:0-0", "0")
        a = parseversion("0:0:0-0-0")
        assert dpkg_version_compare(a, b) == 0

    @expectedFailure
    def test_version_parse_fails_with_multiple_colons_while_dpkg_pass4(self):
        b = DPKG_VERSION_OBJECT(0, "0-0:0", "0")
        a = parseversion("0:0-0:0-0")
        assert dpkg_version_compare(a, b) == 0

    @expectedFailure
    def test_version_parse_fails_with_multiple_colons_while_dpkg_pass5(self):
        #  Test valid characters in upstream version.
        b = DPKG_VERSION_OBJECT(0, "09azAZ.-+~:", "0")
        a = parseversion("0:09azAZ.-+~:-0")
        assert dpkg_version_compare(a, b) == 0

    @expectedFailure
    def test_version_parse_handles_invalid_chars_in_dpkg1(self):
        #  Test valid characters in revision.
        b = DPKG_VERSION_OBJECT(0, "0", "azAZ09.+~")
        a = parseversion("0:0-azAZ09.+~")
        assert dpkg_version_compare(a, b) == 0

    def test_version_parse_handles_valid_chars_in_revision(self):
        #  Test valid characters in revision.
        b = DPKG_VERSION_OBJECT(0, "0", "azA.+~Z09")
        a = parseversion("0:0-azA.+~Z09")
        assert dpkg_version_compare(a, b) == 0

    def test_version_parse_handles_invalid_chars_in_dpkg2(self):
        #  Test version with leading and trailing spaces.
        b = DPKG_VERSION_OBJECT(0, "0", "1")
        a = parseversion("      0:0-1")
        assert dpkg_version_compare(a, b) == 0
        a = parseversion("0:0-1      ")
        assert dpkg_version_compare(a, b) == 0
        a = parseversion("      0:0-1      ")
        assert dpkg_version_compare(a, b) == 0

    def test_version_parse_raise_exception_on_multiple_colons(self):
        self.assertRaises(ValueError, parseversion, "0:0-0:0-0")
        self.assertRaises(ValueError, parseversion, "0:0:0:0-0")
        self.assertRaises(ValueError, parseversion, "0:0:0-0-0")
        self.assertRaises(ValueError, parseversion, "0:0-0:0-0")
        self.assertRaises(ValueError, parseversion, "0:09azAZ.-+~:-0")
        self.assertRaises(ValueError, parseversion, "0:0-azAZ09.+~")

    def test_version_parse_exceptions(self):

        #  Test empty version.
        self.assertRaises(ValueError, parseversion, "")
        self.assertRaises(ValueError, parseversion, " ")

        #  Test empty upstream version after epoch.
        self.assertRaises(ValueError, parseversion, "0:")

        #  Test empty epoch in version.
        self.assertRaises(ValueError, parseversion, ":1.0")

        #  Test empty revision in version.
        self.assertRaises(ValueError, parseversion, "1.0-")

        #  Test version with embedded spaces.
        self.assertRaises(ValueError, parseversion, "0:0 0-1")

        #  Test version with negative epoch.
        self.assertRaises(ValueError, parseversion, "-1:0-1")

        #  Test invalid characters in epoch.
        self.assertRaises(ValueError, parseversion, "a:0-0")
        self.assertRaises(ValueError, parseversion, "A:0-0")

        #  Test version with huge epoch.
        # self.assertRaises(ValueError, parseversion, "999999999999999999999999:0-1")

        #  Test invalid empty upstream version.
        self.assertRaises(ValueError, parseversion, "-0")
        self.assertRaises(ValueError, parseversion, "0:-0")

        #  Test upstream version not starting with a digit
        self.assertRaises(ValueError, parseversion, "0:abc3-0")

        #  Test invalid characters in upstream version.
        for p in "!#@$%&/|\\<>()[]{},_=*^'":
            verstr = '0:0a' + p + '-0'
            self.assertRaises(ValueError, parseversion, verstr)

        #  Test invalid characters in revision.
        self.assertRaises(ValueError, parseversion, "0:0-0:0")

        for p in "!#@$%&/|\\<>()[]{}:,_=*^'":
            verstr = '0:0-0' + p
            self.assertRaises(ValueError, parseversion, verstr)
