# Debian packaging tools: Utility functions.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: January 27, 2017
# URL: https://github.com/xolox/python-deb-pkg-tools
#
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
# Debian packaging tools: Relationship parsing and evaluation.
#

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os


def find_debian_architecture():
    """
    Find the Debian architecture of the current environment.

    Uses :func:`os.uname()` to determine the current machine architecture
    (the fifth value returned by :func:`os.uname()`) and translates it into
    one of the `machine architecture labels`_ used in the Debian packaging
    system:

    ====================  ===================
    Machine architecture  Debian architecture
    ====================  ===================
    ``i686``              ``i386``
    ``x86_64``            ``amd64``
    ``armv6l``            ``armhf``
    ====================  ===================

    When the machine architecture is not listed above, this function falls back
    to the external command ``dpkg-architecture -qDEB_BUILD_ARCH`` (provided by
    the ``dpkg-dev`` package). This command is not used by default because:

    1. deb-pkg-tools doesn't have a strict dependency on ``dpkg-dev``.
    2. The ``dpkg-architecture`` program enables callers to set the current
       architecture and the exact semantics of this are unclear to me at the
       time of writing (it can't automagically provide a cross compilation
       environment, so what exactly does it do?).

    :returns: The Debian architecture (a string like ``i386``, ``amd64``,
              ``armhf``, etc).
    :raises: :exc:`~executor.ExternalCommandFailed` when the
             ``dpkg-architecture`` program is not available or reports an
             error.

    .. _machine architecture labels: https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Architecture
    .. _more architectures: https://www.debian.org/ports/index.en.html#portlist-released
    """
    _sysname, _nodename, _release, _version, machine = os.uname()
    if machine == 'i686':
        return 'i386'
    elif machine == 'x86_64':
        return 'amd64'
    elif machine == 'armv6l':
        return 'armhf'
    else:
        raise Exception('unknown machine')
