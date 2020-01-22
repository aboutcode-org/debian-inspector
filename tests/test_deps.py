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

    def test_architecture_restriction_parsing(self):
        """Test the parsing of architecture restrictions."""
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

    def test_relationship_evaluation_combination_AND_works_with_version(self):
        relationship_set = deps.parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
        assert not relationship_set.matches('python', '2.5')
        assert relationship_set.matches('python', '2.6')
        assert relationship_set.matches('python', '2.7')
        assert not relationship_set.matches('python', '3.0')
        assert relationship_set.matches('python', '3.4')
        assert list(relationship_set.names) == ['python']

    def test_relationship_evaluation_works_without_version_against_versioned(self):
        # Testing for matches without providing a version is valid (should not
        # raise an error) but will never match a relationship with a version.
        relationship_set = deps.parse_depends('python (>= 2.6), python (<< 3)')
        assert relationship_set.matches('python', '2.7')
        assert not relationship_set.matches('python')
        assert list(relationship_set.names) == ['python']

    def test_relationship_evaluation_works_misc_cases(self):
        # Distinguishing between packages whose name was matched but whose
        # version didn't match vs packages whose name wasn't matched.
        relationship_set = deps.parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')

        # name and version match
        assert relationship_set.matches('python', '2.7') is True

        # name matched, version didn't
        assert relationship_set.matches('python', '2.5') is False

        # name didn't match
        assert relationship_set.matches('python2.6') is None

        # name in alternative matched, version didn't
        assert relationship_set.matches('python', '3.0') is False
        assert list(relationship_set.names) == ['python']
