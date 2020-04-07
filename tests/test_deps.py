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

import re
import unittest

from debut import deps


class DepsTestCase(unittest.TestCase):

    def test_relationship_parsing(self):
        relationship_set = deps.parse_depends('foo, bar (>= 1) | baz')
        expected = deps.AndRelationships(relationships=(
            deps.Relationship(name='foo'),
            deps.OrRelationships(relationships=(
                deps.VersionedRelationship(name='bar', operator='>=', version='1'),
                deps.Relationship(name='baz')))))
        assert expected == relationship_set

    def test_relationship_parsing_single_relationship(self):
        expected = deps.AndRelationships(relationships=(
            deps.VersionedRelationship(name='foo', operator='=', version='1.0'),))
        assert expected == deps.parse_depends('foo (=1.0)')

    def test_relationship_parsing_raise_valueerror_for_invalid_relationship(self):
        self.assertRaises(ValueError, deps.parse_depends, 'foo (bar) (baz)')
        self.assertRaises(ValueError, deps.parse_depends, 'foo (bar baz qux)')

    def test_parse_depends(self):
        depends = deps.parse_depends('python (>= 2.6), python (<< 3)')
        expected = deps.AndRelationships(relationships=(
            deps.VersionedRelationship(name='python', operator='>=', version='2.6'),
            deps.VersionedRelationship(name='python', operator='<<', version='3'))
        )
        assert expected == depends
        assert not depends.matches('python', '2.5')
        assert depends.matches('python', '2.6')
        assert depends.matches('python', '2.7')

    def test_parse_alternatives_with_no_alternative(self):
        depends = deps.parse_alternatives('python2.6')
        expected = deps.Relationship(name='python2.6')
        assert expected == depends

    def test_parse_alternatives(self):
        depends = deps.parse_alternatives('python2.6 | python2.7')
        expected = deps.OrRelationships(relationships=(
            deps.Relationship(name='python2.6'),
            deps.Relationship(name='python2.7'))
        )
        assert expected == depends

    def test_architecture_restriction_parsing(self):
        relationship_set = deps.parse_depends('qux [i386 amd64]')
        assert relationship_set.relationships[0].name == 'qux'
        assert len(relationship_set.relationships[0].architectures) == 2
        assert 'i386' in relationship_set.relationships[0].architectures
        assert 'amd64' in relationship_set.relationships[0].architectures

    def test_relationships_objects_as_strings(self):
        def strip(text):
            return re.sub(r'\s+', '', text)
        relationship_set = deps.parse_depends('foo, bar(>=1)|baz[i386]')
        expected = 'foo, bar (>= 1) | baz [i386]'
        assert expected == str(relationship_set)

        expected = deps.AndRelationships(relationships=(
            deps.Relationship(name='foo'),
            deps.OrRelationships(relationships=(
                deps.VersionedRelationship(name='bar', operator='>=', version='1'),
                deps.Relationship(name='baz', architectures=('i386',))))))
        assert expected == relationship_set

    def test_relationship_evaluation_works_without_version(self):
        relationship_set = deps.parse_depends('python')
        assert relationship_set.matches('python')
        assert not relationship_set.matches('python2.7')
        assert list(relationship_set.names) == ['python']

    def test_relationship_evaluation_alternative_OR_works_without_version(self):
        relationship_set = deps.parse_depends('python2.6 | python2.7')
        assert not relationship_set.matches('python2.5')
        assert relationship_set.matches('python2.6')
        assert relationship_set.matches('python2.7')
        assert not relationship_set.matches('python3.0')
        assert sorted(relationship_set.names) == ['python2.6', 'python2.7']

    def test_relationship_evaluation_works_without_version_against_versioned(self):
        # Testing for matches without providing a version is valid (should not
        # raise an error) but will never match a relationship with a version.
        relationship_set = deps.parse_depends('python (>= 2.6), python (<< 3)')
        assert relationship_set.matches('python', '2.7')
        assert not relationship_set.matches('python')
        assert list(relationship_set.names) == ['python']

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
        assert list(relationship_set.names) == ['python']

    def test_parse_depends_misc(self):
        dependencies = deps.parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
        expected = deps.AndRelationships(relationships=(
            deps.VersionedRelationship(name='python', operator='>=', version='2.6'),
            deps.OrRelationships(relationships=(
                deps.VersionedRelationship(name='python', operator='<<', version='3'),
                deps.VersionedRelationship(name='python', operator='>=', version='3.4')
            ,))
        ,))
        assert expected == dependencies

        expected = 'python (>= 2.6), python (<< 3) | python (>= 3.4)'
        assert expected == str(dependencies)

    def test_parse_relationship(self):
        rel = deps.parse_relationship('python')
        assert deps.Relationship(name='python') == rel
        rel = deps.parse_relationship('python (<< 3)')
        assert deps.VersionedRelationship(name='python', operator='<<', version='3') == rel
