#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os.path
import json
import shutil
import sys

if sys.version_info[:2] >= (3, 6):
    OrderedDict = dict
else:
    from collections import OrderedDict

from commoncode.system import py2
from commoncode.system import py3
from commoncode import testcase


class JsonTester(testcase.FileBasedTesting):
    test_data_dir = os.path.join(os.path.dirname(__file__), 'data')

    def check_json(self, results, expected_loc, regen=False):
        """
        Helper to test a results Python native object against an expected JSON
        file at expected_loc.
        """
        expected_loc = self.get_test_loc(expected_loc, exists=not regen)

        if regen:
            regened_exp_loc = self.get_temp_file()
            if py2:
                wmode = 'wb'
            if py3:
                wmode = 'w'
            with open(regened_exp_loc, wmode) as ex:
                json.dump(results, ex, indent=2, separators=(',', ': '))

            expected_dir = os.path.dirname(expected_loc)
            if not os.path.exists(expected_dir):
                os.makedirs(expected_dir)
            shutil.copy(regened_exp_loc, expected_loc)

        with open(expected_loc, 'rb') as ex:
            expected = json.load(ex, encoding='utf-8', object_pairs_hook=OrderedDict)

        assert json.dumps(expected, indent=2) == json.dumps(results, indent=2)

    def check_file(self, results, expected_loc, regen=False):
        """
        Helper to test a results text string against an expected file at
        expected_loc.
        """
        expected_loc = self.get_test_loc(expected_loc, exists=not regen)

        if regen:
            regened_exp_loc = self.get_temp_file()
            with open(regened_exp_loc, 'w') as ex:
                ex.write(results)

            expected_dir = os.path.dirname(expected_loc)
            if not os.path.exists(expected_dir):
                os.makedirs(expected_dir)
            shutil.copy(regened_exp_loc, expected_loc)

        with open(expected_loc) as ex:
            expected = ex.read()

        assert expected == results
