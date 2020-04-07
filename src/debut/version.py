#
# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debut/

# Copyright [2017] The Climate Corporation (https://climate.com)

# Copyright (c) 2018 Peter Odding
# Author: Peter Odding <peter@peterodding.com>
# URL: https://github.com/xolox/python-deb-pkg-tools

# SPDX-License-Identifier: Apache-2.0 AND MIT


from __future__ import absolute_import
from __future__ import unicode_literals

from functools import cmp_to_key

from attr import asdict
from attr import attrs
from attr import attrib


"""
Parse, compare and sort Debian package versions.

This module is an implementation of the version comparison and sorting algorithm
described at
https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version

This has been substantially modified and enhanced from the original python-dpkg
Dpkg class by Nathan J. Meh and team from The Climate Corporation to extract
only the subset that does the version comparison
https://github.com/TheClimateCorporation/python-dpkg ...
So much so that little of this code may still looks like the original.

In addition code from python-deb-pkg-tools by Peter Odding <peter@peterodding.com>
at https://github.com/xolox/python-deb-pkg-tools has also been mixed in.


Some examples:

#### Compare two arbitrary version strings

    >>> from debut import debver
    >>> debver.compare_versions('0:1.0-test1', '0:1.0-test2')
    -1
    >>> debver.compare_versions('1.0', '0.6')
    1
    >>> debver.compare_versions('2:1.0', '1:1.0')
    -1

#### Use Version as a key function to sort a list of version strings

    >>> from debut.debver import Version
    >>> sorted(['0:1.0-test1', '1:0.0-test0', '0:1.0-test2'] , key=Version.from_string)
    ['0:1.0-test1', '0:1.0-test2', '1:0.0-test0']

"""


@attrs(
    eq=False,
    order=False,
    frozen=True,
    hash=False,
    slots=True,
    str=False
)
class Version(object):
    """
    Rich comparison of Debian package versions as first-class Python objects.

    The :class:`Version` class is a subclass of the built in :class:`str` type
    that implements rich comparison according to the version sorting order
    defined in the Debian Policy Manual. Use it to sort Debian package versions
    from oldest to newest in ascending version order like this:

      >>> from debut.version import Version
      >>> unsorted = ['0.1', '0.5', '1.0', '2.0', '3.0', '1:0.4', '2:0.3']
      >>> print([str(v) for v in sorted(Version.from_string(s) for s in unsorted)])
      ['0.1', '0.5', '1.0', '2.0', '3.0', '1:0.4', '2:0.3']

    This example uses 'epoch' numbers (the numbers before the colons) to
    demonstrate that this version sorting order is different from regular
    sorting and 'natural order sorting'.
    """

    # Copyright (c) 2018 Peter Odding

    # Debian packaging tools: Version comparison.
    # Original-Author: Peter Odding <peter@peterodding.com>
    # Original-URL: https://github.com/xolox/python-deb-pkg-tools
    # heavily modified for debut

    epoch = attrib(default=0)
    upstream = attrib(default=None)
    revision = attrib(default=None)

    def __str__(self, *args, **kwargs):
        if self.epoch:
            template = '{epoch}:{upstream}'
        else:
            template = '{upstream}'

        if self.revision is not None and self.revision != '0':
            template += '-{revision}'

        return template.format(**self.to_dict())

    def __repr__(self, *args, **kwargs):
        return str(self)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if type(self) is type(other):
            return eval_constraint(self, '=', other)
        else:
            return NotImplemented

    def __ne__(self, other):
        if type(self) is type(other):
            return not eval_constraint(self, '=', other)
        else:
            return NotImplemented

    def __lt__(self, other):
        if type(self) is type(other):
            return eval_constraint(self, '<<', other)
        else:
            return NotImplemented

    def __le__(self, other):
        if type(self) is type(other):
            return eval_constraint(self, '<=', other)
        else:
            return NotImplemented

    def __gt__(self, other):
        if type(self) is type(other):
            return eval_constraint(self, '>>', other)
        else:
            return NotImplemented

    def __ge__(self, other):
        if type(self) is type(other):
            return eval_constraint(self, '>=', other)
        else:
            return NotImplemented

    @classmethod
    def from_string(cls, version):
        epoch, upstream, revision = get_evr(version)
        return cls(epoch=epoch, upstream=upstream, revision=revision)

    def compare(self, other_version):
        return compare_versions(self, other_version)

    def to_dict(self):
        return asdict(self)


def eval_constraint(version1, operator, version2):
    """
    Evaluate a versions constraint where two Debian package versions are
    compared with an operator such as < or >. Return True if the constraint is
    satisfied and False otherwise.
    """

    # Copyright (c) 2018 Peter Odding
    # Debian packaging tools: Version comparison.
    # Origial-Author: Peter Odding <peter@peterodding.com>
    # Origial-URL: https://github.com/xolox/python-deb-pkg-tools

    result = compare_versions(version1, version2)

    return ((operator == '<<' and result < 0) or
            (operator == '>>' and result > 0) or
            (operator in ('<', '<=') and result <= 0) or
            (operator in ('>', '>=') and result >= 0) or
            (operator == '=' and result == 0))


def get_epoch(version):
    """
    Return a tuple of (epoch, remainder) from a `version` string.
    epoch is an integer.
    """
    if ':' not in version:
        return 0, version

    if version.startswith(':') or version.endswith(':'):
        raise ValueError('Invalid epoch with leading or trailing colon: {}'.format(version))

    left, _, right = version.partition(':')
    if left.isdigit():
        epoch = int(left)
        remainder = right
        return epoch, remainder

    raise ValueError('Invalid epoch: must be digits: {}'.format(version))


def get_upstream(version):
    """
    Return a tuple of (upstream version, revision) from a `version` string.
    Return '0' for revision if absent.
    """
    left, _, right = version.rpartition('-')
    if left and right:
        upstream = left
        revision = right
    else:
        # no hyphens means no debian version, also valid.
        upstream = version
        revision = '0'
    return upstream, revision


def get_evr(version):
    """
    Return a tuple of (epoch, upstream version, revision) from a `version`
    string.
    """
    e, remainder = get_epoch(version)
    v, r = get_upstream(remainder)
    return e, v, r


def get_alphas(revision):
    """
    Return a tuple of the first non-digit characters of a revision (which
    may be empty) and the remaining characters.
    """
    # get the index of the first digit
    for i, char in enumerate(revision):
        if char.isdigit():
            if i == 0:
                return '', revision
            return revision[0:i], revision[i:]
    # string is entirely alphas
    return revision, ''


def get_digits(revision):
    """
    Return a tuple of the first integer characters of a revision (which
    may be empty) and the remainder.
    """
    # If the string is empty, return (0,'')
    if not revision:
        return 0, ''
    # get the index of the first non-digit
    for i, char in enumerate(revision):
        if not char.isdigit():
            if i == 0:
                return 0, revision
            return int(revision[0:i]), revision[i:]
    # string is entirely digits
    return int(revision), ''


def listify(revision):
    """
    Split a revision string into a list of alternating between strings and
    numbers, padded on either end to always be "str, int, str, int..." and
    always be of even length.  This allows us to trivially implement the
    comparison algorithm described at
    http://debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
    """
    result = []
    while revision:
        rev_1, remainder = get_alphas(revision)
        rev_2, remainder = get_digits(remainder)
        result.extend([rev_1, rev_2])
        revision = remainder
    return result


def compare_strings(a, b):
    """
    Compare two Debian package version string sections with a lexical sort
    algorithm and return cmp-like values.
    Return 0 if a=b, 1 if a>b and -1 if a<b.

        The lexical comparison is a comparison of ASCII values modified so that
        all the letters sort earlier than all the non-letters and so that a
        tilde sorts before anything, even the end of a part.
    """

    if a == b:
        return 0
    try:
        for i, char in enumerate(a):
            if char == b[i]:
                continue
            # "a tilde sorts before anything, even the end of a part"
            # (emptyness)
            if char == '~':
                return -1
            if b[i] == '~':
                return 1
            # "all the letters sort earlier than all the non-letters"
            if char.isalpha() and not b[i].isalpha():
                return -1
            if not char.isalpha() and b[i].isalpha():
                return 1
            # otherwise lexical sort
            if ord(char) > ord(b[i]):
                return 1
            if ord(char) < ord(b[i]):
                return -1
    except IndexError:
        # a is longer than b but otherwise equal, hence greater
        # ...except for goddamn tildes
        if char == '~':
            return -1
        return 1
    # if we get here, a is shorter than b but otherwise equal, hence lesser
    # ...except for goddamn tildes
    if b[len(a)] == '~':
        return 1
    return -1


def compare_revisions(a, b):
    """
    Compare two revision strings as described at
    https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
    and return cmp-like values.

    Return 0 id a==b, 1 if a>b and -1 if a<b.
    """
    if a == b:
        return 0
    # listify pads results so that we will always be comparing ints to ints
    # and strings to strings (at least until we fall off the end of a list)
    al = listify(a)
    bl = listify(b)
    if al == bl:
        return 0
    try:
        for i, item in enumerate(al):
            assert isinstance(item, bl[i].__class__)
            # if the items are equal, next
            if item == bl[i]:
                continue
            # numeric comparison
            if isinstance(item, int):
                if item > bl[i]:
                    return 1
                if item < bl[i]:
                    return -1
            else:
                # string comparison
                return compare_strings(item, bl[i])
    except IndexError:
        # a is longer than b but otherwise equal, hence greater
        return 1
    # rev1 is shorter than rev2 but otherwise equal, hence lesser
    return -1


def compare_versions(a, b):
    """
    Compare two Debian package version strings or Version instances,
    suitable for passing to list.sort().

    Return 0 id a=b, 1 if a>b and -1 if a<b.
    """
    if not isinstance(a, Version):
        a = Version.from_string(a)
    if not isinstance(b, Version):
        b = Version.from_string(b)

    # if epochs differ, immediately return the newer one
    if a.epoch < b.epoch:
        return -1
    if a.epoch > b.epoch:
        return 1

    # then, compare the upstream versions
    upstreams = compare_revisions(a.upstream, b.upstream)
    if upstreams != 0:
        return upstreams

    # then, compare the revisions
    revisions = compare_revisions(a.revision, b.revision)
    if revisions != 0:
        return revisions

    # at this point, the versions are equal, but due to an interpolated
    # zero in either the epoch or the debian version
    return 0


def compare_versions_key(x):
    """
    Return a key version function suitable for use in sorted().
    """
    return cmp_to_key(compare_versions)(x)


def compare_strings_key(x):
    """
    Return a key string function suitable for use in sorted().
    """
    return cmp_to_key(compare_strings)(x)
