#
# Copyright (c) nexB Inc. and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/debian-inspector for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#


# legacy module for backward compat
import warnings
warnings.warn("debut module is deprecated. Use debian_inspector instead.", DeprecationWarning, stacklevel=1)
from debian_inspector.coverage import *
