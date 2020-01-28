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

import sys
if sys.version_info[:2] >= (3, 6):
    OrderedDict = dict
else:
    from collections import OrderedDict
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

    """
    output_fields = OrderedDict()
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
