#
# Copyright (c) nexB Inc. and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0 AND MIT
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/debian-inspector for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
# Copyright (c) 2018 Peter Odding
# Author: Peter Odding <peter@peterodding.com>
# URL: https://github.com/xolox/python-deb-pkg-tools


import re
import unittest

from debian_inspector import deps


class DepsTestCase(unittest.TestCase):

    def test_relationship_parsing(self):
        relationship_set = deps.parse_depends('foo, bar (>= 1) | baz')
        expected = deps.AndRelationships(relationships=(
            deps.Relationship(name='foo'),
            deps.OrRelationships(relationships=(
                deps.VersionedRelationship(name='bar', operator='>=', version='1'),
                deps.Relationship(name='baz')))))
        assert relationship_set == expected

    def test_relationship_parsing_single_relationship(self):
        expected = deps.AndRelationships(relationships=(
            deps.VersionedRelationship(name='foo', operator='=', version='1.0'),))
        assert deps.parse_depends('foo (=1.0)') == expected

    def test_relationship_parsing_raise_valueerror_for_invalid_relationship(self):
        self.assertRaises(ValueError, deps.parse_depends, 'foo (bar) (baz)')
        self.assertRaises(ValueError, deps.parse_depends, 'foo (bar baz qux)')

    def test_parse_depends(self):
        depends = deps.parse_depends('python (>= 2.6), python (<< 3)')
        expected = deps.AndRelationships(relationships=(
            deps.VersionedRelationship(name='python', operator='>=', version='2.6'),
            deps.VersionedRelationship(name='python', operator='<<', version='3'))
        )
        assert depends == expected
        assert not depends.matches('python', '2.5')
        assert depends.matches('python', '2.6')
        assert depends.matches('python', '2.7')

    def test_parse_alternatives_with_no_alternative(self):
        depends = deps.parse_alternatives('python2.6')
        expected = deps.Relationship(name='python2.6')
        assert depends == expected

    def test_parse_alternatives(self):
        depends = deps.parse_alternatives('python2.6 | python2.7')
        expected = deps.OrRelationships(relationships=(
            deps.Relationship(name='python2.6'),
            deps.Relationship(name='python2.7'))
        )
        assert depends == expected

    def test_architecture_restriction_parsing(self):
        relationship_set = deps.parse_depends('qux [i386 amd64]')
        assert 'qux' == relationship_set.relationships[0].name
        assert 2 == len(relationship_set.relationships[0].architectures)
        assert 'i386' in relationship_set.relationships[0].architectures
        assert 'amd64' in relationship_set.relationships[0].architectures

    def test_relationships_objects_as_strings(self):

        def strip(text):
            return re.sub(r'\s+', '', text)

        relationship_set = deps.parse_depends('foo, bar(>=1)|baz[i386]')
        expected = 'foo, bar (>= 1) | baz [i386]'
        assert str(relationship_set) == expected

        expected = deps.AndRelationships(relationships=(
            deps.Relationship(name='foo'),
            deps.OrRelationships(relationships=(
                deps.VersionedRelationship(name='bar', operator='>=', version='1'),
                deps.Relationship(name='baz', architectures=('i386',))))))
        assert relationship_set == expected

    def test_relationship_evaluation_works_without_version(self):
        relationship_set = deps.parse_depends('python')
        assert relationship_set.matches('python')
        assert not relationship_set.matches('python2.7')
        assert ['python'] == list(relationship_set.names)

    def test_relationship_evaluation_alternative_OR_works_without_version(self):
        relationship_set = deps.parse_depends('python2.6 | python2.7')
        assert not relationship_set.matches('python2.5')
        assert relationship_set.matches('python2.6')
        assert relationship_set.matches('python2.7')
        assert not relationship_set.matches('python3.0')
        assert ['python2.6', 'python2.7'] == sorted(relationship_set.names)

    def test_relationship_evaluation_works_without_version_against_versioned(self):
        # Testing for matches without providing a version is valid (should not
        # raise an error) but will never match a relationship with a version.
        relationship_set = deps.parse_depends('python (>= 2.6), python (<< 3)')
        assert relationship_set.matches('python', '2.7')
        assert not relationship_set.matches('python')
        assert ['python'] == list(relationship_set.names)

    def test_relationship_evaluation_combination_AND_works_with_version(self):
        # Distinguishing between packages whose name was matched but whose
        # version didn't match vs packages whose name wasn't matched.
        relationship_set = deps.parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
        # name matched, version didn't
        assert relationship_set.matches('python', '2.5') is False
        # name didn't match
        assert relationship_set.matches('python2.6') is None
        # name in alternative matched, version didn't
        assert relationship_set.matches('python', '3.0') is False

        # name and version match
        assert relationship_set.matches('python', '2.7') is True
        assert relationship_set.matches('python', '2.6')
        assert relationship_set.matches('python', '3.4')
        assert ['python'] == list(relationship_set.names)

    def test_parse_depends_misc(self):
        dependencies = deps.parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
        expected = deps.AndRelationships(relationships=(
            deps.VersionedRelationship(name='python', operator='>=', version='2.6'),
            deps.OrRelationships(relationships=(
                deps.VersionedRelationship(name='python', operator='<<', version='3'),
                deps.VersionedRelationship(name='python', operator='>=', version='3.4')
            ,))
        ,))
        assert dependencies == expected

        expected = 'python (>= 2.6), python (<< 3) | python (>= 3.4)'
        assert str(dependencies) == expected

    def test_parse_relationship(self):
        rel = deps.parse_relationship('python')
        assert rel == deps.Relationship(name='python')
        rel = deps.parse_relationship('python (<< 3)')
        assert rel == deps.VersionedRelationship(name='python', operator='<<', version='3')

    def test_parse_depends_complex_cases_is_idempotent(self):
        depends = [
            'clamav-freshclam (>= 0.103.2+dfsg) | clamav-data, libc6 (>= 2.15), libclamav9 (>= 0.103.2), '
                'libcurl3 (>= 7.16.2), libjson-c2 (>= 0.10), libssl1.0.0 (>= 1.0.0), zlib1g (>= 1:1.2.3.3)',
            'sysvinit-utils (>= 2.86.ds1-62), insserv (>> 1.12.0-10)',
            'libgimp2.0 (>= 2.8.16), libgimp2.0 (<= 2.8.16-z)',
            'zlib1g (>= 1:1.1.4), python:any (>= 2.6.6-7~)',
            'git (>> 1:2.34.1), git (<< 1:2.34.1-.)',
            'libnspr4 (>= 2:4.13.1), libnspr4 (<= 2:4.13.1-0ubuntu0.16.04.1.1~)',
            'libc6 (>> 2.23), libc6 (<< 2.24)',
            'libptexenc1 (>= 2015.20160222.37495-1ubuntu0.1), libptexenc1 (<< 2015.20160222.37495-1ubuntu0.1.1~), '
                'libkpathsea6 (>= 2015.20160222.37495-1ubuntu0.1), libkpathsea6 (<< 2015.20160222.37495-1ubuntu0.1.1~), '
                'libsynctex1 (>= 2015.20160222.37495-1ubuntu0.1), libsynctex1 (<< 2015.20160222.37495-1ubuntu0.1.1~), '
                'libtexlua52 (>= 2015.20160222.37495-1ubuntu0.1), libtexlua52 (<< 2015.20160222.37495-1ubuntu0.1.1~), '
                'libtexluajit2 (>= 2015.20160222.37495-1ubuntu0.1), libtexluajit2 (<< 2015.20160222.37495-1ubuntu0.1.1~)',
            'libldb1 (<< 2:1.1.25~), libldb1 (>> 2:1.1.24~)',
            'libnettle6 (= 3.2-1ubuntu0.16.04.2), libhogweed4 (= 3.2-1ubuntu0.16.04.2), libgmp10-dev, dpkg (>= 1.15.4) | install-info',
            'libkf5widgetsaddons-data (= 5.18.0-0ubuntu1), libc6 (>= 2.14), libqt5core5a (>= 5.5.0), '
                'libqt5gui5 (>= 5.3.0) | libqt5gui5-gles (>= 5.3.0), libqt5widgets5 (>= 5.2.0), libstdc++6 (>= 4.1.1)',
            'libnuma1 (= 2.0.11-1ubuntu1.1), libc6-dev | libc-dev',
            'perl, perl (>= 5.11.2) | libextutils-cbuilder-perl, perl (>= 5.12) | libextutils-parsexs-perl, '
                'perl (>= 5.13.9) | libmodule-metadata-perl, perl (>= 5.13.9) | libversion-perl (>= 1:0.8700), '
                'perl (>= 5.19.5) | libtest-harness-perl (>= 3.29), perl (>= 5.21.3) | libcpan-meta-perl (>= 2.142060)',
            'libc6 (>= 2.14), libglib2.0-0 (>= 2.37.3), libgtk-3-0 (>= 3.11.5), libgtksourceview-3.0-1 (>= 3.17.3), '
                'libpeas-1.0-0 (>= 1.0.0), libzeitgeist-2.0-0 (>= 0.9.9), dconf-gsettings-backend | gsettings-backend, '
                'python3 (<< 3.6), python3 (>= 3.5~), python3.5, gedit (>= 3.18), gedit (<< 3.19), gir1.2-git2-glib-1.0, '
                'gir1.2-glib-2.0, gir1.2-gtk-3.0, gir1.2-gtksource-3.0, gir1.2-gucharmap-2.90, gir1.2-pango-1.0, gir1.2-peas-1.0, '
                'gir1.2-vte-2.91, gir1.2-zeitgeist-2.0, python3-gi, python3-gi-cairo, python3-cairo, python3-dbus',
        ]

        for depend in depends:
            assert str(deps.parse_depends(depend)) == depend
