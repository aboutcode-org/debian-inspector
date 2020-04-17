#
# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debut/

# Copyright (c) 2018 Peter Odding
# Author: Peter Odding <peter@peterodding.com>
# URL: https://github.com/xolox/python-deb-pkg-tools

# SPDX-License-Identifier: Apache-2.0 AND MIT


from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from os import path
import unittest

from debut import debcon
from debut import deps
from debut import package
from debut import version


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


class DebArchiveTestCase(unittest.TestCase):

    def test_DebArchive_from_filename(self):
        fn = '/var/cache/apt/archives/python2.7_2.7.3-0ubuntu3.4_amd64.deb'
        debarch = package.DebArchive.from_filename(fn)
        expected = package.DebArchive(
            name='python2.7',
            version=version.Version(epoch=0, upstream='2.7.3', revision='0ubuntu3.4'),
            architecture='amd64',
            original_filename=fn)
        assert expected == debarch


class ControlTestCase(unittest.TestCase):

    def test_parse_control_fields_1(self):
        deb822_package = debcon.Debian822([
            ('Package', 'python-py2deb'),
            ('Depends', 'python-deb-pkg-tools, python-pip, python-pip-accel'),
            ('Installed-Size', '42'),
        ])
        parsed_info = debcon.parse_control_fields(deb822_package)
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

    def test_parse_control_fields_2(self):
        unparsed_fields = debcon.deb822_from_string('''
Package: python3.4-minimal
Version: 3.4.0-1+precise1
Architecture: amd64
Installed-Size: 3586
Pre-Depends: libc6 (>= 2.15)
Depends: libpython3.4-minimal (= 3.4.0-1+precise1), libexpat1 (>= 1.95.8), libgcc1 (>= 1:4.1.1), zlib1g (>= 1:1.2.0), foo | bar
Recommends: python3.4
Suggests: binfmt-support
Conflicts: binfmt-support (<< 1.1.2)
''')

        expected = {
            'Architecture': 'amd64',
            'Conflicts': 'binfmt-support (<< 1.1.2)',
            'Depends': 'libpython3.4-minimal (= 3.4.0-1+precise1), libexpat1 (>= 1.95.8), '
                       'libgcc1 (>= 1:4.1.1), zlib1g (>= 1:1.2.0), foo | bar',
            'Installed-Size': '3586',
            'Package': 'python3.4-minimal',
            'Pre-Depends': 'libc6 (>= 2.15)',
            'Recommends': 'python3.4',
            'Suggests': 'binfmt-support',
            'Version': '3.4.0-1+precise1',
        }


        assert expected == unparsed_fields.to_dict(normalize_names=True)

        parsed_fields = debcon.parse_control_fields(unparsed_fields)

        expected = {
            'Architecture': 'amd64',
            'Conflicts': deps.AndRelationships(relationships=(
                deps.VersionedRelationship(name=u'binfmt-support', operator=u'<<', version=u'1.1.2')
            ,)),
            'Depends': deps.AndRelationships(relationships=(
                deps.VersionedRelationship(name=u'libpython3.4-minimal', operator=u'=', version=u'3.4.0-1+precise1'),
                deps.VersionedRelationship(name=u'libexpat1', operator=u'>=', version=u'1.95.8'),
                deps.VersionedRelationship(name=u'libgcc1', operator=u'>=', version=u'1:4.1.1'),
                deps.VersionedRelationship(name=u'zlib1g', operator=u'>=', version=u'1:1.2.0'),
                deps.OrRelationships(relationships=(
                    deps.Relationship(name=u'foo'),
                    deps.Relationship(name=u'bar')
                ,))
            ),),
            'Installed-Size': 3586,
            'Package': 'python3.4-minimal',
            'Pre-Depends': deps.AndRelationships(relationships=(
                deps.VersionedRelationship(name=u'libc6', operator=u'>=', version=u'2.15')
            ,)),
            'Recommends': deps.AndRelationships(relationships=(deps.Relationship(name=u'python3.4'),)),
            'Suggests': deps.AndRelationships(relationships=(deps.Relationship(name=u'binfmt-support'),)),
            'Version': '3.4.0-1+precise1'}

        assert expected == parsed_fields
