#
# Copyright (c) nexB Inc. and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/debian-inspector for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

import itertools
from collections import defaultdict
from email import utils as email_utils

from attr import attrib
from attr import attrs
from attr import Factory
from attr import fields_dict

from debian_inspector import deb822
from debian_inspector import debcon

"""
Utilities to parse Debian machine readable copyright files (aka. dep5)
"""


@attrs
class LicenseField(debcon.FieldMixin):
    name = attrib(default=None)
    text = attrib(default=None)

    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls):
            return value
        lic = debcon.DescriptionField.from_value(value)
        return cls(name=lic.synopsis, text=lic.text)

    def dumps(self, **kwargs):
        lic = debcon.DescriptionField(self.name, self.text)
        return lic.dumps(**kwargs).strip()

    def has_doc_reference(self):
        """
        Return True if this license contains a reference to a Debian shared
        license file in the /usr/share/common-licenses directory.
        """
        return self.text and '/usr/share/common-licenses' in self.text


@attrs
class CopyrightStatementField(debcon.FieldMixin):
    """
    Conventionally (but not in the spec) each line in a copyright is a space-
    separated tuple of (year range, holder). If it cannot be parsed, the holder
    contains all text.
    This field represents one line, e.g. one statememt.
    """
    # TODO: add line tracking
    holder = attrib()
    year_range = attrib(default=None)

    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls):
            return value
        value = value or ''
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        value = ' '.join(value.split())
        year_range, _, holder = value.partition(' ')
        year_range = year_range.strip()
        holder = holder.strip()
        if not is_year_range(year_range):
            holder = value
            year_range = None
        return cls(holder=holder, year_range=year_range)

    def dumps(self, **kwargs):
        cop = self.holder
        if self.year_range:
            cop = '{} {}'.format(self.year_range, cop)
        return cop.strip()


def is_year_range(text):
    """
    Return True if `text` is a year range.
    """
    if not text:
        return
    if all(c.isdigit() for c in text):
        return True

    digit_punct = set('''!"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ 1234567890''')
    if all(c in digit_punct for c in text) and any(c.isdigit() for c in text):
        return True


@attrs
class CopyrightField(debcon.FieldMixin):
    """
    This represents a single "Copyright: field which is a plain formatted text
    but is conventionally a list of copyrights statements one per line
    """
    statements = attrib(default=Factory(list))

    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls):
            return value
        statements = []
        if value:
            statements = [
                CopyrightStatementField.from_value(v)
                for v in debcon.line_separated(value)]
        return cls(statements=statements)

    def dumps(self, **kwargs):
        dumped = [
            s.dumps(**kwargs) if hasattr(s, 'dumps') else str(s)
            for s in self.statements
        ]
        return '\n           '.join(dumped).strip()


@attrs
class MaintainerField(debcon.FieldMixin):
    """
    https://www.debian.org/doc/debian-policy/ch-controlfields#s-f-maintainer
    5.6.2. Maintainer
    """
    name = attrib()
    email_address = attrib(default=None)

    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls):
            return value
        name = email_address = None
        if value:
            value = value.strip()
            name, email_address = email_utils.parseaddr(value)
            if not name:
                name = value
                email_address = None
            return cls(name=name, email_address=email_address)

    def dumps(self, **kwargs):
        name = self.name
        if self.email_address:
            name = '{} <{}>'.format(name, self.email_address)
        return name.strip()


@attrs
class ParagraphMixin(debcon.FieldMixin):

    # a mapping of {field_name: (start_line, end_line)} for each field
    line_numbers_by_field = attrib(default=Factory(dict))

    def get_field_line_numbers(self, field_name):
        """
        Return a tuple of (start_line, end_line) for the ``field_name`` field.
        """
        return self.line_numbers_by_field[field_name]

    @classmethod
    def from_header_fields(cls, header_fields, all_extra=False):
        """
        Return a paragraph built from a list of debian_inspector.deb822.Header.
        If ``all_extra`` is True, treat all data as "extra_data".
        """
        if all_extra:
            # if everything is "extra_data" this means there are no known names.
            known_names = set()
        else:
            known_names = set(fields_dict(cls))

        para_data = {}
        para_data['extra_data'] = extra_data = {}
        para_data['line_numbers_by_field'] = line_numbers_by_field = {}

        duplicated_field_name_suffix = 1
        seen_names = set()
        for header_field in header_fields:
            value = header_field.text
            if value:
                name = header_field.name.replace('-', '_')

                # if there are duplicated fields, we keep them all, rename them
                # and they will go to extra_data
                if name in seen_names:
                    name = f'{name}_{duplicated_field_name_suffix}'
                    duplicated_field_name_suffix += 1
                seen_names.add(name)

                if name in known_names:
                    mapping = para_data
                else:
                    mapping = extra_data
                assert name not in mapping

                mapping[name] = value

                line_numbers_by_field[name] = (header_field.start_line, header_field.end_line,)

        try:
            return cls(**para_data)
        except Exception as e:
            raise Exception(cls, para_data) from e

    def to_dict(self, with_lines=False):
        data = {}

        for name in fields_dict(self.__class__):
            if name in ('extra_data' , 'line_numbers_by_field'):
                continue

            value = getattr(self, name)
            if value:
                if hasattr(value, 'dumps'):
                    value = value.dumps()
                data[name] = value

        for name, value in getattr(self, 'extra_data', {}).items():
            if value:
                # always treat these extra values as formatted
                value = value and debcon.as_formatted_text(value)
            data[name] = value
        if with_lines:
            data['line_numbers_by_field'] = self.line_numbers_by_field
        return data

    def dumps(self, **kwargs):
        text = []
        for name, value in self.to_dict().items():
            if value:
                name = name.replace('_', '-')
                name = debcon.normalize_control_field_name(name)
                text.append('{}: {}'.format(name, value))
        return '\n'.join(text).strip()

    def is_empty(self):
        """
        Return True if all fields are empty
        """
        return not any(self.to_dict().values())

    def has_extra_data(self):
        return getattr(self, 'extra_data', None)


@attrs
class CatchAllParagraph(ParagraphMixin):
    """
    A catch-all paragraph: everything is fed to the extra_data. Every field is
    treated as formatted text.
    """
    extra_data = attrib(default=Factory(dict))

    @classmethod
    def from_header_fields(cls, header_fields):
        return super(CatchAllParagraph, cls).from_header_fields(
            header_fields=header_fields,
            all_extra=True,
        )

    def is_all_unknown(self):
        """
        Return True if this is an "unknown" field.
        We use the "unknown" field name for things that do not have a name.
        """
        return all(k == 'unknown' for k in self.to_dict())

    def is_valid(self, strict=False):
        if strict:
            return False
        return not self.is_all_unknown()


@attrs
class CopyrightHeaderParagraph(ParagraphMixin):
    """
    The header paragraph.

    https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/#header-paragraph
    """
    # Default should be:
    # https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
    # but we do not know yet if this a structured machine-readable format
    format = debcon.SingleLineField.attrib(default=None)

    upstream_name = debcon.SingleLineField.attrib(default=None)
    # TODO: each may be a Maintainer
    upstream_contact = debcon.LineSeparatedField.attrib(default=None)

    source = debcon.FormattedTextField.attrib(default=None)
    disclaimer = debcon.FormattedTextField.attrib(default=None)
    copyright = CopyrightField.attrib(default=None)
    license = LicenseField.attrib(default=None)
    comment = debcon.FormattedTextField.attrib(default=None)

    # This field is not yet official but seen in use. See:
    # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=685506
    files_excluded = debcon.AnyWhiteSpaceSeparatedField.attrib(default=None)

    # This is an overflow of extra unknown fields for this paragraph
    extra_data = attrib(default=Factory(dict))

    def is_valid(self, strict=False):
        valid = is_machine_readable_copyright(self.format.value)
        if strict:
            valid = valid and not self.has_extra_data()
        return valid


def is_machine_readable_copyright(text):
    """
    Return True if a text is for a machine-readable copyright format.
    """
    return text and text[:100].lower().startswith((
        'format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0',
        'format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0',
    ))


@attrs
class CopyrightFilesParagraph(ParagraphMixin):
    """
    A "files" paragraph with files, copyright, license and comment fields.

    https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/#files-paragraph
    """
    files = debcon.AnyWhiteSpaceSeparatedField.attrib(default=None)
    copyright = CopyrightField.attrib(default=None)
    license = LicenseField.attrib(default=None)
    comment = debcon.FormattedTextField.attrib(default=None)

    # this is an overflow of extra unknown fields for this paragraph
    extra_data = attrib(default=Factory(dict))

    def dumps(self, **kwargs):
        if self.is_empty():
            return 'Files: '
        else:
            return ParagraphMixin.dumps(self)

    def is_empty(self):
        """
        Return True if this is empty.
        """
        return not any([
            self.files.values,
            self.license.name,
            self.license.text,
            self.comment.text,
            self.copyright.statements,
            self.extra_data,
        ])

    def is_valid(self, strict=False):
        valid = (
            self.files.values
            and self.copyright.statements
            and self.license.name or self.license.text)
        if strict:
            valid = valid and not self.has_extra_data()
        return valid


@attrs
class CopyrightLicenseParagraph(ParagraphMixin):
    """
    A standalone license paragraph with license and comment fields, but no files.

    https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/#stand-alone-license-paragraph
    """
    license = LicenseField.attrib(default=None)
    comment = debcon.FormattedTextField.attrib(default=None)

    # this is an overflow of extra unknown fields for this paragraph
    extra_data = attrib(default=Factory(dict))

    def is_empty(self):
        """
        Return True if this is empty (e.g. was crated only because of a
        'License:' empty field.
        """
        return not any([
            self.extra_data,
            self.comment.text,
            self.license.name,
            self.license.text,
        ])

    def dumps(self, **kwargs):
        if self.is_empty():
            return 'License: '
        else:
            return ParagraphMixin.dumps(self)

    def is_valid(self, strict=False):
        valid = self.license.name or (self.license.name and self.license.text)
        if strict:
            valid = valid and not self.has_extra_data()
        return valid


@attrs
class DebianCopyright(object):
    """
    A machine-readable debian copyright file.
    See https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
    """
    paragraphs = attrib(default=Factory(list))

    def __attrs_post_init__(self, *args, **kwargs):
        self.merge_contiguous_unknown_paragraphs()
        self.fold_contiguous_empty_license_followed_by_unknown()

    @classmethod
    def from_text(cls, text):
        header_fields_groups = deb822.get_header_fields_groups(text)
        return cls.from_header_fields_groups(header_fields_groups)

    @classmethod
    def from_file(cls, location):
        header_fields_groups = deb822.get_header_fields_groups_from_file(location)
        return cls.from_header_fields_groups(header_fields_groups)

    @classmethod
    def from_header_fields_groups(cls, header_fields_groups):
        """
        Return a DebianCopyright from a ``header_fields_groups`` list of list of
        HeaderField.
        """
        collected_paragraphs = []
        for header_fields in header_fields_groups:
            field_names = set([hf.name for hf in header_fields])

            if 'format'in field_names or 'format-specification' in field_names:
                # let's be flexible and assume that we have a header if some
                # format field is there
                cp = CopyrightHeaderParagraph.from_header_fields(header_fields)

            elif 'files' in field_names:
                # do we have a "files"? this is a file header_fields
                cp = CopyrightFilesParagraph.from_header_fields(header_fields)

            elif 'license' in field_names:
                cp = CopyrightLicenseParagraph.from_header_fields(header_fields)

            else:
                # we catch all the rest as junk to be flexible and miss nothing
                cp = CatchAllParagraph.from_header_fields(header_fields)

            collected_paragraphs.append(cp)

        return cls(collected_paragraphs)

    def dumps(self, **kwargs):
        dumped = [p.dumps(**kwargs) for p in self.paragraphs]
        dumped = '\n\n'.join(dumped)
        return dumped + '\n'

    def to_dict(self, with_lines=False):
        return {
            'paragraphs': [p.to_dict(with_lines=with_lines) for p in self.paragraphs]
        }

    def get_header(self):
        """
        Return the header paragraph or None.
        """
        headers = [
            p for p in self.paragraphs
            if isinstance(p, CopyrightHeaderParagraph)]
        if headers:
            return headers[0]

    def merge_contiguous_unknown_paragraphs(self):
        """
        Update self.paragraphs, merging contiguous unknown-only
        CatchAllParagraph paragraphs in one.
        """
        paragraphs = []
        for typ, contigs in itertools.groupby(self.paragraphs, type):
            contigs = list(contigs)
            if typ != CatchAllParagraph or len(contigs) == 1:
                paragraphs.extend(contigs)
            else:
                if all(p.is_all_unknown() for p in contigs):
                    values = []
                    start_line = -1
                    end_line = -1
                    for para in contigs:
                        values.extend(k for k in para.to_dict().values())
                        values.append('')
                        # the new start and end lines are the maximal start and
                        # end lines of each contiguous paragraph
                        start_line = min(start_line, para.start_line)
                        end_line = max(end_line, para.end_line)

                    values = debcon.from_formatted_lines(values)
                    line_numbers_by_field = {'unknown':(start_line, end_line,)}
                    paragraphs.append(
                        CatchAllParagraph(
                            unknown=values,
                            line_numbers_by_field=line_numbers_by_field,
                        )
                    )
                else:
                    paragraphs.extend(contigs)

        self.paragraphs = paragraphs

    def fold_contiguous_empty_license_followed_by_unknown(self):
        """
        Update self.paragraphs, such that a CatchAllParagraph paragraph with
        "unknown" as license text is merged into a preceding empty (e.g. without
        any text) CopyrightLicenseParagraph paragraph.
        """
        if len(self.paragraphs) <= 2:
            return

        folded_previous = False
        paragraphs = []
        # iterate on (p1,p2), (p2,p3)....
        for para1, para2 in zip(self.paragraphs, self.paragraphs[1:]):
            if folded_previous:
                folded_previous = False
                continue

            if (isinstance(para1, CopyrightLicenseParagraph)
                and para1.is_empty()
                and isinstance(para2, CatchAllParagraph)
                and para2.is_all_unknown()
            ):
                para1.license.name = ''
                para1.license.text = para2.to_dict().get('unknown', '')

                # The updated CopyrightLicenseParagraph paragraph lines extend
                # from its original start line to the end line of the
                # CatchAllParagraph
                start_line, _end_line = para1.line_numbers_by_field['license']
                _start_line, end_line = para2.line_numbers_by_field['unknown']
                para1.line_numbers_by_field['license'] = (start_line, end_line,)
                folded_previous = True

            paragraphs.append(para1)

        if not folded_previous:
            paragraphs.append(para2)
        self.paragraphs = paragraphs

    def is_valid(self, strict=False):
        """
        Return True if this is a valid Debian Copyright file.
        If `strict` is True, validate strictly against the spec.
        """
        if not self.paragraphs:
            return False
        has_header = False
        has_files = False
        has_license = False
        has_unknown = False
        first = self.paragraphs[0]
        paragraphs = sorted(self.paragraphs, key=lambda x: repr(type(x)))
        for typ, paras in itertools.groupby(paragraphs, type):
            paras = list(paras)
            if typ == CopyrightHeaderParagraph:
                if not strict:
                    has_header = True

                elif (len(paras) == 1 and paras[0].is_valid(strict)
                      and paras[0] == first):
                    has_header = True

            elif typ == CopyrightFilesParagraph:
                has_files = all(p.is_valid(strict) for p in paras)

            elif typ == CopyrightLicenseParagraph:
                has_license = all(p.is_valid(strict) for p in paras)

            elif typ == CatchAllParagraph:
                has_unknown = all(p.is_valid(strict) for p in paras)

            else:
                # unknown paragraph type
                return False

        valid = has_header and has_files or (has_license and has_files)
        if strict:
            return valid and has_unknown
        else:
            return valid
