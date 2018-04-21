#!/usr/bin/env python
#
# Copyright 2018 The JsCodeStyle Authors.
# Copyright 2008 The Closure Linter Authors. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the runner module."""


import StringIO
import unittest

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from jscodestyle import runner
from jscodestyle.common import error
from jscodestyle.common import tokens


class LimitedDocTest(unittest.TestCase):

    def test_is_limited_doc_check(self):
        self.assertTrue(runner._IsLimitedDocCheck('foo_test.js', ['_test.js']))
        self.assertFalse(runner._IsLimitedDocCheck('foo_bar.js', ['_test.js']))

        self.assertTrue(runner._IsLimitedDocCheck(
            'foo_moo.js', ['moo.js', 'quack.js']))
        self.assertFalse(runner._IsLimitedDocCheck(
            'foo_moo.js', ['woof.js', 'quack.js']))


class RunnerTest(unittest.TestCase):

    def setUp(self):
        self.mock_error_handler = MagicMock()

    def test_run_on_missing_file(self):
        runner.Run('does_not_exist.js', self.mock_error_handler)

        self.mock_error_handler.HandleFile.assert_called_once_with(
            'does_not_exist.js', None)
        self.assertIsInstance(
            self.mock_error_handler.HandleError.call_args[0][0],
            error.Error)
        self.mock_error_handler.FinishFile.assert_called_once()

    def test_bad_tokenization(self):
        source = StringIO.StringIO(_BAD_TOKENIZATION_SCRIPT)
        runner.Run('foo.js', self.mock_error_handler, source)

        #  self.mock_error_handler.HandleFile.assert_called_once_with(
        #    'foo.js', tokens.Token)
        self.assertEquals(
            self.mock_error_handler.HandleFile.call_args[0][0],
            'foo.js')
        self.assertIsInstance(
            self.mock_error_handler.HandleFile.call_args[0][1],
            tokens.Token)
        self.assertIsInstance(
            self.mock_error_handler.HandleError.call_args[0][0],
            error.Error)
        self.mock_error_handler.FinishFile.assert_called_once()


_BAD_TOKENIZATION_SCRIPT = """
function foo () {
  var a = 3;
  var b = 2;
  return b + a; /* Comment not closed
}
"""


if __name__ == '__main__':
    unittest.main()
