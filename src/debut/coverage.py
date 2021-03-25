#
# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debian_inspector/

# SPDX-License-Identifier: Apache-2.0

# legacy module for backward compat
import warnings
warnings.warn("debut module is deprecated. Use debian_inspector instead.", DeprecationWarning, stacklevel=1)
from debian_inspector.coverage import *
