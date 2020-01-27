#
# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debut/

# Copyright (c) 2018 Peter Odding
# Author: Peter Odding <peter@peterodding.com>
# URL: https://github.com/xolox/python-deb-pkg-tools

# SPDX-License-Identifier: Apache-2.0 AND MIT


"""
Functions to manipulate Debian control files.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from debut import debcon
from debut import deps


DEFAULT_CONTROL_FIELDS = {
    'Architecture': 'all',
    'Priority': 'optional',
    'Section': 'misc',
}


def load_control_file(control_file):
    """
    Load a control file and return the parsed control fields.

    :param control_file: The filename of the control file to load (a string).
    :returns: A dictionary created by :func:`parse_control_fields()`.
    """
    with open(control_file) as handle:
        return parse_control_fields(debcon.Debian822(handle))


DEPS_FIELDS = frozenset([
    # Binary control file fields.
    'Breaks',
    'Conflicts',
    'Depends',
    'Enhances',
    'Pre-Depends',
    'Provides',
    'Recommends',
    'Replaces',
    'Suggests',
    # Source control file fields.
    'Build-Conflicts',
    'Build-Conflicts-Arch',
    'Build-Conflicts-Indep',
    'Build-Depends',
    'Build-Depends-Arch',
    'Build-Depends-Indep',
    'Built-Using',
])


def parse_control_fields(input_fields, deps_fields=DEPS_FIELDS):
    """
    Return an ordered mapping from parsing an`input_fields` mapping of Debian
    control file fields. This applies a few conversions such as:

    - The values of the fields that contain dependencies are parsed
      into Python data structures.

    - The value of some fields such as `Installed-Size` from a string to a
    native type (here an integer).

    Let's look at an example. We start with the raw control file contents so
    you can see the complete input:

    >>> from debut.control import deb822_from_string
    >>> unparsed_fields = deb822_from_string('''
    ... Package: python3.4-minimal
    ... Version: 3.4.0-1+precise1
    ... Architecture: amd64
    ... Installed-Size: 3586
    ... Pre-Depends: libc6 (>= 2.15)
    ... Depends: libpython3.4-minimal (= 3.4.0-1+precise1), libexpat1 (>= 1.95.8), libgcc1 (>= 1:4.1.1), zlib1g (>= 1:1.2.0), foo | bar
    ... Recommends: python3.4
    ... Suggests: binfmt-support
    ... Conflicts: binfmt-support (<< 1.1.2)
    ... ''')

    Here are the control file fields as parsed in dictionary:

    >>> print(repr(unparsed_fields))
    {'Architecture': u'amd64',
     'Conflicts': u'binfmt-support (<< 1.1.2)',
     'Depends': u'libpython3.4-minimal (= 3.4.0-1+precise1), libexpat1 (>= 1.95.8), libgcc1 (>= 1:4.1.1), zlib1g (>= 1:1.2.0), foo | bar',
     'Installed-Size': u'3586',
     'Package': u'python3.4-minimal',
     'Pre-Depends': u'libc6 (>= 2.15)',
     'Recommends': u'python3.4',
     'Suggests': u'binfmt-support',
     'Version': u'3.4.0-1+precise1'}

    Notice the value of the `Depends` line is a comma separated string, i.e. it
    hasn't been parsed. Now here are the control file fields parsed:

    >>> from debut.control import parse_control_fields
    >>> parsed_fields = parse_control_fields(unparsed_fields)
    >>> print(repr(parsed_fields))
    {'Architecture': u'amd64',
     'Conflicts': RelationshipSet(VersionedRelationship(name=u'binfmt-support', operator=u'<<', version=u'1.1.2')),
     'Depends': RelationshipSet(VersionedRelationship(name=u'libpython3.4-minimal', operator=u'=', version=u'3.4.0-1+precise1'),
                                VersionedRelationship(name=u'libexpat1', operator=u'>=', version=u'1.95.8'),
                                VersionedRelationship(name=u'libgcc1', operator=u'>=', version=u'1:4.1.1'),
                                VersionedRelationship(name=u'zlib1g', operator=u'>=', version=u'1:1.2.0'),
                                OrRelationships((Relationship(name=u'foo'), Relationship(name=u'bar')))),
     'Installed-Size': 3586,
     'Package': u'python3.4-minimal',
     'Pre-Depends': AndRelationships((VersionedRelationship(name=u'libc6', operator=u'>=', version=u'2.15'))),
     'Recommends': u'python3.4',
     'Suggests': AndRelationshipSet((Relationship(name=u'binfmt-support'))),
     'Version': u'3.4.0-1+precise1'}
    """
    output_fields = {}
    for name, unparsed_value in input_fields.items():
        name = normalize_control_field_name(name)
        if name in deps_fields:
            parsed_value = deps.parse_depends(unparsed_value)
        elif name == 'Installed-Size':
            parsed_value = int(unparsed_value)
        else:
            parsed_value = unparsed_value
        output_fields[name] = parsed_value
    return output_fields


def normalize_control_field_name(name):
    """
    Return a case-normalized field name string.

    Normalization of control file field names is not really needed when reading
    as we lowercase everything and replace dash to underscore internally, but it
    can help to compare the parsing results to the original file while testing.

    According to the Debian Policy Manual field names are not case-sensitive,
    however a conventional capitalization is most common and not using it may
    break hings.

    http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-controlsyntax
    """
    special_cases = dict(md5sum='MD5sum', sha1='SHA1', sha256='SHA256')
    return '-'.join(special_cases.get(
        w.lower(), w.capitalize()) for w in name.split('-'))


def deb822_from_string(text):
    """
    Return a `debcon.Debian822` object built from a string.
    """
    return debcon.Debian822(textwrap.dedent(text).strip())
