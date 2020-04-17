#
# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debut/

# SPDX-License-Identifier: Apache-2.0


from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os.path
import json
import shutil
from commoncode import testcase


class JsonTester(testcase.FileBasedTesting):
    test_data_dir = os.path.join(os.path.dirname(__file__), 'data')

    def check_json(self, results, expected_loc, regen=False, sort=False):
        """
        Helper to test a results Python native object against an expected JSON
        file at expected_loc.
        """
        expected_loc = self.get_test_loc(expected_loc, exists=not regen)

        if regen:
            regened_exp_loc = self.get_temp_file()
            with open(regened_exp_loc, 'w') as ex:
                json.dump(results, ex, indent=2, separators=(',', ': '))

            expected_dir = os.path.dirname(expected_loc)
            if not os.path.exists(expected_dir):
                os.makedirs(expected_dir)
            shutil.copy(regened_exp_loc, expected_loc)

        with open(expected_loc, 'rb') as ex:
            expected = json.load(ex, encoding='utf-8')
        if sort:
            assert sorted(expected) == sorted(results)
        else:
            assert json.dumps(expected, indent=2) == json.dumps(results, indent=2)

    def check_file(self, results, expected_loc, regen=False, sort=False):
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

        with open(expected_loc, 'rb') as ex:
            expected = ex.read()
            expected = expected.decode('utf-8')
        if sort:
            assert sorted(expected.splitlines()) == sorted(results.splitlines())
        else:
            assert expected == results
