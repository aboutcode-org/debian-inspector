# Copyright 2013 Agustin Henze <tin@sluc.org.ar>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import fnmatch
import os
from os import path
from debut.copyright import CopyrightFilesParagraph


class Coverage(object):
    """
    Helper to compute the "coverage" of a copyright file "files" paragraph. This
    is used to check if all files in a directory are referenced by a one of the
    patterns in a "files" field.
    """

    # TODO: add support for excludes!!!
    def __init__(self, paragraphs, directory):
        self.paragraphs = paragraphs
        self.directory = directory
        self.unmatched = set()
        self.matched = {}

    def is_perfect(self):
        matched, unmatched = self.compute()
        return matched and not unmatched

    def compute(self):
        """
        Compute the coverage and update self.
        """
        paragraphs = [p for p in self.paragraphs 
                      if isinstance(p, CopyrightFilesParagraph)]
        
        for root, _dirs, files in os.walk(self.directory, topdown=True):
            root = path.relpath(root, self.directory)
            paths = [path.join(root, filename) for filename in files]
            self.unmatch |= set(paths)
            for paragraph in paragraphs:
                for pattern in paragraph.files:
                    goodfiles = []
                    if pattern.find(path.sep) == -1:
                        pattern_norm = path.join(path.curdir, pattern)
                        goodfiles.extend(fnmatch.filter(paths, pattern_norm))
                    goodfiles.extend(fnmatch.filter(paths, pattern))
                    self.unmatched -= set(goodfiles)
                    self.matched.update({f: paragraph for f in goodfiles})

        return self.matched, self.unmatched
