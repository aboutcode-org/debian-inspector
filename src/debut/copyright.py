#
# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debut/

# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from email import utils as email_utils
import itertools

from attr import attrib
from attr import attrs
from attr import Factory
from attr import fields_dict

from debut import debcon

"""
Utilities to parse Debian machine readable copyright files (aka. dep5)
"""


@attrs
class LicenseField(debcon.FieldMixin):
    name = attrib(default=None)
    text = attrib(default=None)

    @classmethod
    def from_value(cls, value):
        lic = debcon.DescriptionField.from_value(value)
        return cls(name=lic.synopsis, text=lic.text)

    def dumps(self, sort=False):
        lic = debcon.DescriptionField(self.name, self.text)
        return lic.dumps(sort=sort).strip()

    def has_doc_reference(self):
        """
        Return True if this license has a reference to the Debian shared license included with the distro.
        """
        return self.text and '/usr/share/common-licenses' in self.text


# map of Debian known license keys to actual ScanCode license keys
DEBIAN_LICENSE_KEYS = {
    'public-domain': 'public-domain',
    'Apache': '',
    'Artistic': '',
    'BSD-2-clause': 'bsd-new',
    'BSD-3-clause': 'bsd-simplified',
    'BSD-4-clause': 'bsd-original',
    'ISC': 'isc',
    'CC-BY': 'cc-by-3.0',
    'CC-BY-SA': '',
    'CC-BY-ND': '',
    'CC-BY-NC': '',
    'CC-BY-NC-SA': '',
    'CC-BY-NC-ND': '',
    'CC0': 'cc0-1.0',
    'CDDL': '',
    'CPL': '',
    'EFL': '',
    'Expat': 'mit',
    'GPL': '',
    'LGPL': '',
    'GFDL': '',
    'GFDL-NIV': '',
    'LPPL': '',
    'MPL': '',
    'Perl': '',
    'Python': 'python',
    'QPL': '',
    'W3C': '',
    'Zlib': 'zlib',
    'Zope': '',
    }


@attrs
class CopyrightStatementField(debcon.FieldMixin):
    """
    Conventionally (but not in the spec) each line in a copyright is a space-
    separated tuple of (year range, holder). If it cannot be parsed, the holder
    contains all text.
    This field represents one line, e.g. one statememt.
    """
    holder = attrib()
    year_range = attrib(default=None)

    @classmethod
    def from_value(cls, value):
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

    def dumps(self, sort=False):
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
    This represnts a single "Copyright: field which is a plain formatted text
    but is conventionally a list of copyrights statements one per line
    """
    statements = attrib(default=Factory(list))

    @classmethod
    def from_value(cls, value):
        statements = []
        if value:
            statements = [
                CopyrightStatementField.from_value(v)
                for v in debcon.line_separated(value)]
        return cls(statements=statements)

    def dumps(self, sort=False):
        dumped = [s.dumps() for s in self.statements]
        if sort:
            dumped = sorted(dumped)
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
        name = email_address = None
        if value:
            value = value.strip()
            name, email_address = email_utils.parseaddr(value)
            if not name:
                name = value
                email_address = None
            return cls(name=name, email_address=email_address)

    def dumps(self, sort=False):
        name = self.name
        if self.email_address:
            name = '{} <{}>'.format(name, self.email_address)
        return name.strip()


@attrs
class ParagraphMixin(debcon.FieldMixin):

    @classmethod
    def from_dict(cls, data):
        assert isinstance(data, dict)
        known_names = list(fields_dict(cls))
        known_data = {}
        known_data['extra_data'] = extra_data = {}
        for key, value in data.items():
            key = key.replace('-', '_')
            if value:
                if isinstance(value, list):
                    value = '\n'.join(value)
                if key in known_names:
                    known_data[key] = value
                else:
                    extra_data[key] = value

        return cls(**known_data)

    def to_dict(self):
        data = {}
        for field_name in fields_dict(self.__class__):
            if field_name == 'extra_data':
                continue
            field_value = getattr(self, field_name)
            if field_value:
                if hasattr(field_value, 'dumps'):
                    field_value = field_value.dumps()
                data[field_name] = field_value

        for field_name, field_value in getattr(self, 'extra_data', {}).items():
            if field_value:
                # always treat these extra values as formatted
                field_value = field_value and debcon.as_formatted_text(field_value)
            data[field_name] = field_value
        return data

    def dumps(self, sort=False):
        text = []
        for field_name, field_value in self.to_dict().items():
            if field_value:
                field_name = field_name.replace('_', '-')
                field_name = debcon.normalize_control_field_name(field_name)
                text.append('{}: {}'.format(field_name, field_value))
        if sort:
            text = sorted(text)
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
    def from_dict(cls, data):
        # Stuff all data in the extra_data mapping as FormattedTextField
        assert isinstance(data, dict)
        known_data = {}
        for key, value in data.items():
            key = key.replace('-', '_')
            known_data[key] = debcon.FormattedTextField.from_value(value)
        return cls(extra_data=known_data)

    def to_dict(self):
        data = {}
        for field_name, field_value in self.extra_data.items():
            if field_value:
                if hasattr(field_value, 'dumps'):
                    field_value = field_value.dumps()
                data[field_name] = field_value
        return data

    def is_all_unknown(self):
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
    # Default would be https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/')
    format = debcon.SingleLineField.attrib(default=None)
    upstream_name = debcon.SingleLineField.attrib(default=None)
    # TODO: each may be a Maintainer
    upstream_contact = debcon.LineSeparatedField.attrib(default=None)
    source = debcon.FormattedTextField.attrib(default=None)
    disclaimer = debcon.FormattedTextField.attrib(default=None)
    copyright = CopyrightField.attrib(default=None)
    license = LicenseField.attrib(default=None)
    comment = debcon.FormattedTextField.attrib(default=None)
    # not yet official but seen in use. See https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=685506
    files_excluded = debcon.AnyWhiteSpaceSeparatedField.attrib(default=None)

    # this is an overflow of extra unknown fields for this paragraph
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

    def dumps(self, sort=False):
        if self.is_empty():
            return 'Files: '
        else:
            return ParagraphMixin.dumps(self, sort=sort)

    def is_empty(self):
        """
        Return True if this is empty.
        """
        return (
            not self.files.values
            and not self.extra_data
            and not self.comment.text
            and not self.copyright.statements
            and not self.license.name
            and not self.license.text)

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
        return (
            not self.extra_data
            and not self.comment.text
            and not self.license.name
            and not self.license.text)

    def dumps(self, sort=False):
        if self.is_empty():
            return 'License: '
        else:
            return ParagraphMixin.dumps(self, sort=sort)

    def is_valid(self, strict=False):
        valid = self.license.name or (self.license.name and self.license.text)
        if strict:
            valid = valid and not self.has_extra_data()
        return valid


@attrs
class DebianCopyright(object):
    """
    A machine-readable debian copyright file.
    https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
    """
    paragraphs = attrib(default=Factory(list))

    def __attrs_post_init__(self, *args, **kwargs):
        self.merge_contiguous_unknown_paragraphs()
        self.fold_contiguous_empty_license_followed_by_unknown()

    @classmethod
    def from_text(cls, text):
        paragraphs = iter(debcon.get_paragraphs_data(text))
        return cls._from_paragraph_data(paragraphs)

    @classmethod
    def from_file(cls, location):
        paragraphs = iter(debcon.get_paragraphs_data_from_file(location))
        return cls._from_paragraph_data(paragraphs)

    @classmethod
    def _from_paragraph_data(cls, paragraphs):
        collected_paragraphs = []
        for data in paragraphs:
            if 'format' in data or 'format-specification' in data:
                # let's be flexible and assume that we have a header if the
                # format field is there
                cp = CopyrightHeaderParagraph.from_dict(data)
            elif 'files' in data:
                # do we have a files? that's enough to say this is a file paragraph
                cp = CopyrightFilesParagraph.from_dict(data)
            elif 'license' in data:
                cp = CopyrightLicenseParagraph.from_dict(data)
            else:
                # we catch all the rest as junk to be flexible and miss nothing
                cp = CatchAllParagraph.from_dict(data)
            collected_paragraphs.append(cp)
        return cls(collected_paragraphs)

    def dumps(self, sort=False):
        dumped = [p.dumps(sort=sort) for p in self.paragraphs]
        if sort:
            dumped = sorted(dumped)
        dumped = '\n\n'.join(dumped)
        return dumped + '\n'

    def to_dict(self):
        data = {}
        data['paragraphs'] = [p.to_dict() for p in self.paragraphs]
        return data

    def get_header(self):
        headers = [
            p for p in self.paragraphs
            if isinstance(p, CopyrightHeaderParagraph)]
        if headers:
            return headers[0]

    def merge_contiguous_unknown_paragraphs(self):
        """
        Update self.paragraphs, merging contiguous unknown-only Catchall
        paragraphs in one.
        """
        paragraphs = []
        for typ, contigs in itertools.groupby(self.paragraphs, type):
            contigs = list(contigs)
            if typ != CatchAllParagraph or len(contigs) == 1:
                paragraphs.extend(contigs)
            else:
                if all(p.is_all_unknown() for p in contigs):
                    values = []
                    for para in contigs:
                        values.extend(k for k in para.to_dict().values())
                        values.append('')
                    values = debcon.from_formatted_lines(values)
                    paragraphs.append(
                        CatchAllParagraph.from_dict(dict(unknown=values)))
                else:
                    paragraphs.extend(contigs)
        self.paragraphs = paragraphs

    def fold_contiguous_empty_license_followed_by_unknown(self):
        """
        Update self.paragraphs, merging an empty License paragraph followied by
        unknown-only Catchall paragraphs in one.
        """
        if len(self.paragraphs) <= 2:
            return

        paragraphs = []
        # iterate on (p1,p2), (p2,p3)....
        folded_previous = False
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
        if strict:
            return has_header and (has_files or (has_license and has_files)) and has_unknown
        else:
            return has_header and (has_files or (has_license and has_files))
