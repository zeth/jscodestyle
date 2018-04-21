#!/usr/bin/env python
# Copyright 2018 The JsCodeStyle Authors.
# Copyright 2007 The Closure Linter Authors. All Rights Reserved.
#
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

"""Checks JavaScript files for common style guide violations.

gjslint.py is designed to be used as a PRESUBMIT script to check for javascript
style guide violations.  As of now, it checks for the following violations:

  * Missing and extra spaces
  * Lines longer than 80 characters
  * Missing newline at end of file
  * Missing semicolon after function declaration
  * Valid JsDoc including parameter matching

Someday it will validate to the best of its ability against the entirety of the
JavaScript style guide.

This file is a front end that parses arguments and flags.  The core of the code
is in tokenizer.py and checker.py.
"""

import argparse


class JsCodeStyle(object):
    """This class is a front end that parses arguments and flags."""
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-u', '--unix_mode',
            help='emit warnings in standard unix format',
            action='store_true')
        parser.add_argument(
            '-b', '--beep',
            help='do not beep when errors are found',
            action='store_false')
        parser.add_argument(
            '-t', '--time',
            help='emit timing statistics',
            action='store_true')
        parser.add_argument(
            '-c', '--check_html',
            help='check javascript in html files',
            action='store_true')
        parser.add_argument(
            '-s', '--summary',
            help='show an error count summary',
            action='store_true')
        parser.add_argument(
            '-q', '--quiet',
            help=('minimize logged messages. '
                  'Most useful for per-file linting, such as that '
                  'performed by the presubmit linter service.'),
            action='store_true')
        parser.add_argument(
            '-a', '--additional_extensions',
            help=('comma separated list of additional file '
                  'extensions (not js) that should be treated as '
                  'JavaScript files.'))
        parser.add_argument(
            '-m', '--multiprocess',
            help=('disable parallelised linting using the '
                  'multiprocessing module; this may make debugging easier.'),
            action='store_true')

        parser.parse_args()

    def check(self):
        """Check the JavaScript files for style."""
        pass


def main():
    """Used when called as a command line script."""
    style_checker = JsCodeStyle()
    style_checker.check()


if __name__ == '__main__':
    main()
