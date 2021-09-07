#
# Copyright (c) nexB Inc. and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/debian-inspector for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

"""
A parser for deb822  (RFC822, RFC2822, and similar) data file used by Debian
control and copyright files, and several similar formats.

For details, see:
- https://www.debian.org/doc/debian-policy/ch-controlfields
- https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
- https://datatracker.ietf.org/doc/rfc2822/


Why yet another RFC822/Debian822 parser?

This module exists becausee no other parser module (in particular the stadard
email module) is able to track the start and end line numbers of each email
header and we need line number to trace license detection and data collecion in
Debian manifests, in particular in copyright files.
"""

import attr

from debian_inspector.debcon import read_text_file


def get_header_fields_groups(text):
    """
    Yield lists of HeaderField for each paragraph in a ``text`` each separated
    by one or more empty lines. Raise Exceptions on errors.
    """
    return get_header_fields_groups_from_lines(NumberedLine.lines_from_text(text))


def get_header_fields_groups_from_file(location):
    """
    Yield lists of HeaderField for each paragraph in a control file at
    ``location``. Raise Exceptions on errors.
    """
    if not location:
        return []
    return get_header_fields_groups(read_text_file(location))


def get_header_fields_groups_from_lines(numbered_lines):
    """
    Yield lists of HeaderField for each paragraph in a ``numbered_lines`` list
    of NumberedLine. Raise Exceptions on errors.
    """
    header_fields_group = []
    current_header_field = None
    for line in numbered_lines:

        # One or more blank line terminates a paragraph of header_fields_group
        # and starts a new one.
        if line.is_blank():
            if header_fields_group:
                header_fields_group = clean_header_fields(header_fields_group)
                yield header_fields_group
                header_fields_group = []
                current_header_field = None
            else:
                # skip empty lines in between paragraphs
                pass

        # a header field continuation line
        elif current_header_field and line.is_continuation():
            current_header_field.add_continuation_line(line)

        # a new header field line
        elif line.is_header_field():
            current_header_field = HeaderField.from_line(line)
            if not current_header_field:
                raise Exception(f'Invalid header field line: {line}')
            header_fields_group.append(current_header_field)
        else:
            # an unknown line:  we yield this as its own group
            if header_fields_group:
                header_fields_group = clean_header_fields(header_fields_group)
                yield header_fields_group
            # craft a synthetic header with name "unknown"
            yield [HeaderField(name='unknown', lines=[line])]
            header_fields_group = []
            current_header_field = None

    # last header fields group if any
    if header_fields_group:
        header_fields_group = clean_header_fields(header_fields_group)
        yield header_fields_group


def clean_header_fields(header_fields):
    """
    Clean and validate a list of HeaderField.
    """
    for hf in (header_fields or []):
        hf.rstrip()
    headers_by_name = {hf.name for hf in header_fields}
    if len(headers_by_name) != len(header_fields):
        raise Exception(
            f'Invalid duplicated header field in: {header_fields}'
        )
    return header_fields


@attr.s(slots=True)
class NumberedLine:
    """
    A text line that tracks its absolute line number. Numbers start at 1.
    """
    number = attr.ib()
    value = attr.ib()

    def is_empty(self):
        return not self.value

    def is_blank(self):
        return not self.value.strip()

    def is_header_field(self):
        return ':' in self.value and not self.is_continuation()

    def is_continuation(self):
        return self.value.startswith((' ', '\t'))

    @classmethod
    def lines_from_text(cls, text):
        """
        Return a list of Line from a ``text``
        """
        return [
            cls(number=number, value=value)
            for number, value in enumerate(text.splitlines(False), 1)
        ]

    def to_dict(self):
        return attr.asdict(self)


@attr.s(slots=True)
class HeaderField:
    """
    A named HeaderField field with a list of NumberedLines.
    """
    # header field name, normalized as stripped and lowercase
    name = attr.ib(default=None)

    lines = attr.ib(default=attr.Factory(list))

    @property
    def text(self):
        return '\n'.join(l.value for l in self.lines)

    @property
    def start_line(self):
        return self.lines[0].number

    @property
    def end_line(self):
        return self.lines[-1].number

    def rstrip(self):
        """
        Remove the last lines of these lines they are all blank or empty.
        Return self.
        """
        lines = self.lines
        while lines:
            if not lines[-1].value.strip():
                lines.pop()
            else:
                break
        return self

    def add_continuation_line(self, line):
        assert line.is_continuation()
        self.lines.append(
            NumberedLine(number=line.number, value=line.value.rstrip())
        )

    @classmethod
    def from_line(cls, line):
        """
        Parse a ``line`` Line object as a "Name: value" header line and return a
        HeaderField object. Return None if this is not a HeaderField.
        """
        if not line or not line.is_header_field():
            return

        name, _colon, value = line.value.partition(':')
        name = name.strip().lower()
        if not name:
            return

        value = value.strip()
        first_line = NumberedLine(number=line.number, value=value)
        return cls(name=name, lines=[first_line])

    def to_dict(self):
        return attr.asdict(self)
