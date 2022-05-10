#!/usr/bin/python

# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2005 Florian Weimer <fw@deneb.enyo.de>
# Copyright (C) 2006-2007 James Westby <jw+debian@jameswestby.net>
# Copyright (C) 2010 John Wright <jsw@debian.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

# this subset of Python debian tests has been modified to tests version
# comparison and parsing

from unittest import TestCase

from debian_inspector import version


def check_Version_from_string(version_string, epoch, upstream, revision):
    v = version.Version.from_string(version_string)
    result = v.epoch, v.upstream, v.revision
    expected = epoch, upstream, revision
    assert result == expected


def check_compare_versions(version1, operator, version2):
    expected_ops = {
        '==': 0,
        '>': 1,
        '<':-1,
    }
    expected = expected_ops[operator]
    compared = version.compare_versions(version1, version2)
    assert compared == expected


class VersionTests(TestCase):

    def test_Version_from_string(self):
        check_Version_from_string('1:1.4.1-1', 1, '1.4.1', '1')
        check_Version_from_string('7.1.ds-1', 0, '7.1.ds', '1')
        check_Version_from_string('10.11.1.3-2', 0, '10.11.1.3', '2')
        check_Version_from_string('4.0.1.3.dfsg.1-2', 0, '4.0.1.3.dfsg.1', '2')
        check_Version_from_string('0.4.23debian1', 0, '0.4.23debian1', '0')
        check_Version_from_string('1.2.10+cvs20060429-1', 0, '1.2.10+cvs20060429', '1')
        check_Version_from_string('0.2.0-1+b1', 0, '0.2.0', '1+b1')
        check_Version_from_string('4.3.90.1svn-r21976-1', 0, '4.3.90.1svn-r21976', '1')
        check_Version_from_string('1.5+E-14', 0, '1.5+E', '14')
        check_Version_from_string('20060611-0.0', 0, '20060611', '0.0')
        check_Version_from_string('0.52.2-5.1', 0, '0.52.2', '5.1')
        check_Version_from_string('7.0-035+1', 0, '7.0', '035+1')
        check_Version_from_string('1.1.0+cvs20060620-1+2.6.15-8', 0, '1.1.0+cvs20060620-1+2.6.15', '8')
        check_Version_from_string('1.1.0+cvs20060620-1+1.0', 0, '1.1.0+cvs20060620', '1+1.0')
        check_Version_from_string('4.2.0a+stable-2sarge1', 0, '4.2.0a+stable', '2sarge1')
        check_Version_from_string('1.8RC4b', 0, '1.8RC4b', '0')
        check_Version_from_string('0.9~rc1-1', 0, '0.9~rc1', '1')
        check_Version_from_string('2:1.0.4+svn26-1ubuntu1', 2, '1.0.4+svn26', '1ubuntu1')
        check_Version_from_string('2:1.0.4~rc2-1', 2, '1.0.4~rc2', '1')
        self.assertRaises(ValueError, version.Version.from_string, 'a1:1.8.8-070403-1~priv1')

    def test_compare_versions(self):
        check_compare_versions('1.0', '<', '1.1')
        check_compare_versions('1.2', '<', '1.11')
        check_compare_versions('1.0-0.1', '<', '1.1')
        check_compare_versions('1.0-0.1', '<', '1.0-1')
        check_compare_versions('1.0', '==', '1.0')
        check_compare_versions('1.0-0.1', '==', '1.0-0.1')
        check_compare_versions('1:1.0-0.1', '==', '1:1.0-0.1')
        check_compare_versions('1:1.0', '==', '1:1.0')
        check_compare_versions('1.0-0.1', '<', '1.0-1')
        check_compare_versions('1.0final-5sarge1', '>', '1.0final-5')
        check_compare_versions('1.0final-5', '>', '1.0a7-2')
        check_compare_versions('0.9.2-5', '<', '0.9.2+cvs.1.0.dev.2004.07.28-1.5')
        check_compare_versions('1:500', '<', '1:5000')
        check_compare_versions('100:500', '>', '11:5000')
        check_compare_versions('1.0.4-2', '>', '1.0pre7-2')
        check_compare_versions('1.5~rc1', '<', '1.5')
        check_compare_versions('1.5~rc1', '<', '1.5+b1')
        check_compare_versions('1.5~rc1', '<', '1.5~rc2')
        check_compare_versions('1.5~rc1', '>', '1.5~dev0')
