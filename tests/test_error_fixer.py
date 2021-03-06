#!/usr/bin/env python
#
# Copyright 2018 The JsCodeStyle Authors.
# Copyright 2012 The Closure Linter Authors. All Rights Reserved.
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

"""Unit tests for the error_fixer module."""

import unittest
from jscodestyle import error_fixer
from jscodestyle import testutil
from jscodestyle import tokenutil


class ErrorFixerTest(unittest.TestCase):
    """Unit tests for error_fixer."""

    def setUp(self):
        self.error_fixer = error_fixer.ErrorFixer()

    def testDeleteToken(self):
        start_token = testutil.TokenizeSourceAndRunEcmaPass(_TEST_SCRIPT)
        second_token = start_token.next
        self.error_fixer.HandleFile('test_file', start_token)

        self.error_fixer._DeleteToken(start_token)

        self.assertEqual(second_token, self.error_fixer._file_token)

    def testDeleteTokens(self):
        start_token = testutil.TokenizeSourceAndRunEcmaPass(_TEST_SCRIPT)
        fourth_token = start_token.next.next.next
        self.error_fixer.HandleFile('test_file', start_token)

        self.error_fixer._DeleteTokens(start_token, 3)

        self.assertEqual(fourth_token, self.error_fixer._file_token)

    def DoTestFixJsDocPipeNull(self, expected, original):
        _, comments = testutil.ParseFunctionsAndComments(
            '/** @param {%s} */' % original)
        jstype = comments[0].GetDocFlags()[0].jstype
        self.error_fixer.HandleFile('unittest', None)
        self.error_fixer._FixJsDocPipeNull(jstype)
        self.assertEquals(expected, repr(jstype))
        result = tokenutil.TokensToString(jstype.FirstToken()).strip('} */')
        self.assertEquals(expected, result)

    def testFixJsDocPipeNull(self):
        self.DoTestFixJsDocPipeNull('?Object', 'Object|null')
        self.DoTestFixJsDocPipeNull('function(?Object)', 'function(Object|null)')
        self.DoTestFixJsDocPipeNull('function(?Object=)',
                                    'function(Object|null=)')
        self.DoTestFixJsDocPipeNull(
            'function(?(Object)=,null=,?(Object)=):string',
            'function((Object|null)=,null=,(Object|null)=):string')

_TEST_SCRIPT = """\
var x = 3;
"""

if __name__ == '__main__':
    unittest.main()
