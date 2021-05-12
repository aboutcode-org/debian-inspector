#
# Copyright [2017] The Climate Corporation (https://climate.com)
# https://github.com/TheClimateCorporation/python-dpkg
# original author: Nathan J. Meh

# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debian_inspector/

# SPDX-License-Identifier: Apache-2.0

from unittest import TestCase

from debian_inspector import version
from debian_inspector.version import compare_strings
from debian_inspector.version import compare_versions
from debian_inspector.version import Version

"""
Parse, compare and sort Debian package versions.

This has been substantially modified from python-dpkg to extract the version
comparison code.
"""


def get_non_digit_prefix(s):
    val = version.get_non_digit_prefix(list(s))
    return ''.join(val)


def get_digit_prefix(s):
    return version.get_digit_prefix(list(s))


class DebianVersionTest(TestCase):

    def test_Version_from_string_epoch(self):
        assert 0 == Version.from_string('0').epoch
        assert 0 == Version.from_string('0:0').epoch
        assert 1 == Version.from_string('1:0').epoch

    def test_Version_from_string_validates(self):
        self.assertRaises(ValueError, Version.from_string, 'a')
        self.assertRaises(ValueError, Version.from_string, '1a:0')
        self.assertRaises(ValueError, Version.from_string, '0:a.0.0-foo')

    def test_Version_from_string_tuples(self):
        assert (0, '00', '0') == Version.from_string('00').tuple()
        assert (0, '00', '00') == Version.from_string('00-00').tuple()
        assert (0, '0', '0') == Version.from_string('0:0').tuple()
        assert (0, '0', '0') == Version.from_string('0:0-0').tuple()
        assert (0, '0.0', '0') == Version.from_string('0:0.0').tuple()
        assert (0, '0.0', '0') == Version.from_string('0:0.0-0').tuple()
        assert (0, '0.0', '00') == Version.from_string('0:0.0-00').tuple()

    def test_get_non_digit_prefix(self):
        assert '' == get_non_digit_prefix('')
        assert '' == get_non_digit_prefix('0')
        assert '' == get_non_digit_prefix('00')
        assert '' == get_non_digit_prefix('0a')
        assert 'a' == get_non_digit_prefix('a')
        assert 'a' == get_non_digit_prefix('a0')
        assert 'aHAD' == get_non_digit_prefix('aHAD0030')

    def test_get_digit_prefix(self):
        assert 0 == get_digit_prefix('00')
        assert 0 == get_digit_prefix('0')
        assert 0 == get_digit_prefix('0a')
        assert 12 == get_digit_prefix('12a')
        assert 0 == get_digit_prefix('a')
        assert 0 == get_digit_prefix('a0')
        assert 0 == get_digit_prefix('arttr23123')
        assert 123 == get_digit_prefix('123sdf')
        assert 123 == get_digit_prefix('0123sdf')

    def test_compare_strings(self):
        assert -1 == compare_strings('~', '.')
        assert -1 == compare_strings('~', 'a')
        assert -1 == compare_strings('a', '.')
        assert 1 == compare_strings('a', '~')
        assert 1 == compare_strings('.', '~')
        assert 1 == compare_strings('.', 'a')
        assert 0 == compare_strings('.', '.')
        assert 0 == compare_strings('0', '0')
        assert 0 == compare_strings('a', 'a')

    def test_compare_strings_can_sort(self):
        # taken from
        # http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
        result = sorted(['a', '', '~', '~~a', '~~'], key=version.compare_strings_key)
        expected = ['~~', '~~a', '~', '', 'a']
        assert result == expected

    def test_compare_strings_more(self):
        # note that these are testing a single revision string, not the full
        # upstream+debian version.  IOW, "0.0.9-foo" is an upstream or debian
        # revision onto itself, not an upstream of 0.0.9 and a debian of foo.

        # equals
        assert 0 == compare_strings('0', '0')
        assert 0 == compare_strings('0', '00')
        assert 0 == compare_strings('00.0.9', '0.0.9')
        assert 0 == compare_strings('0.00.9-foo', '0.0.9-foo')
        assert 0 == compare_strings('0.0.9-1.00foo', '0.0.9-1.0foo')

        # less than
        assert -1 == compare_strings('0.0.9', '0.0.10')
        assert -1 == compare_strings('0.0.9-foo', '0.0.10-foo')
        assert -1 == compare_strings('0.0.9-foo', '0.0.10-goo')
        assert -1 == compare_strings('0.0.9-foo', '0.0.9-goo')
        assert -1 == compare_strings('0.0.10-foo', '0.0.10-goo')
        assert -1 == compare_strings('0.0.9-1.0foo', '0.0.9-1.1foo')

        # greater than
        assert 1 == compare_strings('0.0.10', '0.0.9')
        assert 1 == compare_strings('0.0.10-foo', '0.0.9-foo')
        assert 1 == compare_strings('0.0.10-foo', '0.0.9-goo')
        assert 1 == compare_strings('0.0.9-1.0foo', '0.0.9-1.0bar')

    def test_compare_versions(self):
        # "This [the epoch] is a single (generally small) unsigned integer.
        # It may be omitted, in which case zero is assumed."
        assert 0 == compare_versions('0.0.0', '0:0.0.0')
        assert 0 == compare_versions('0:0.0.0-foo', '0.0.0-foo')
        assert 0 == compare_versions('0.0.0-a', '0:0.0.0-a')

        # "The absence of a debian_revision is equivalent to a debian_revision of 0."
        assert 0 == compare_versions('0.0.0', '0.0.0-0')
        # tricksy:
        assert 0 == compare_versions('0.0.0', '0.0.0-00')

        # combining the above
        assert 0 == compare_versions('0.0.0-0', '0:0.0.0')

        # explicitly equal
        assert 0 == compare_versions('0.0.0', '0.0.0')
        assert 0 == compare_versions('1:0.0.0', '1:0.0.0')
        assert 0 == compare_versions('0.0.0-10', '0.0.0-10')
        assert 0 == compare_versions('2:0.0.0-1', '2:0.0.0-1')

        # less than
        assert -1 == compare_versions('0.0.0-0', '0:0.0.1')
        assert -1 == compare_versions('0.0.0-0', '0:0.0.0-a')
        assert -1 == compare_versions('0.0.0-0', '0:0.0.0-1')
        assert -1 == compare_versions('0.0.9', '0.0.10')
        assert -1 == compare_versions('0.9.0', '0.10.0')
        assert -1 == compare_versions('9.0.0', '10.0.0')

        assert -1 == compare_versions("1.2.3-1~deb7u1", "1.2.3-1")
        assert -1 == compare_versions("2.7.4+reloaded2-13ubuntu1", "2.7.4+reloaded2-13+deb9u1")
        assert -1 == compare_versions("2.7.4+reloaded2-13", "2.7.4+reloaded2-13+deb9u1")

        # greater than
        assert 1 == compare_versions('0.0.1-0', '0:0.0.0')
        assert 1 == compare_versions('0.0.0-a', '0:0.0.0-1')
        assert 1 == compare_versions('0.0.0-a', '0:0.0.0-0')
        assert 1 == compare_versions('0.0.9', '0.0.1')
        assert 1 == compare_versions('0.9.0', '0.1.0')
        assert 1 == compare_versions('9.0.0', '1.0.0')

        assert 1 == compare_versions("1.2.3-1", "1.2.3-1~deb7u1")
        assert 1 == compare_versions("2.7.4+reloaded2-13+deb9u1", "2.7.4+reloaded2-13ubuntu1")
        assert 1 == compare_versions("2.7.4+reloaded2-13+deb9u1", "2.7.4+reloaded2-13")

        # unicode
        assert -1 == compare_versions(u'2:0.0.44-1', u'2:0.0.44-nobin')
        assert 1 == compare_versions(u'2:0.0.44-nobin', u'2:0.0.44-1')
        assert 0 == compare_versions(u'2:0.0.44-1', u'2:0.0.44-1')
