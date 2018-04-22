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
import sys
import time
import os

# Comment - These are all the tags from gjslint There are way too
# many, we should think what is really useful and cull some.
# Perhaps we should rely more on a config file for advance setups

class JsCodeStyle(object):
    """This class is a front end that parses arguments and flags."""
    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument(
            'paths',
            help='the files to check',
            type=str,
            nargs='*',
            default=sys.stdin)

        parser.add_argument(
            '-u', '--unix_mode',
            help='emit warnings in standard unix format e.g. for Emacs',
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
            '-m', '--multiprocess',
            help=('disable parallelised linting using the '
                  'multiprocessing module; this may make debugging easier.'),
            action='store_true')

        parser.add_argument(
            '-a', '--additional_extensions',
            help=('Additional file extensions (not js) that should '
                  'be treated as JavaScript files e.g. es, es6 or ts.'),
            metavar='ext',
            nargs='+'
        )

        parser.add_argument(
            '-r', '--recurse',
            help=('recurse in to the subdirectories of the given path'),
            action='append',
            nargs='+',
            metavar='dir')

        parser.add_argument(
            '-e', '--exclude_directories',
            help=('exclude the specified directories '
                  '(only applicable along with -r'),
            type=str,
            action='append',
            nargs='+',
            metavar='dir')

        parser.add_argument(
            '-x', '--exclude_files',
            type=str,
            nargs='*',
            help='exclude the specified files',
            action='append',
            metavar='file')

        parser.add_argument(
            '--limited_doc_files',
            help=('List of files with relaxed documentation checks. Will not '
                  'report errors for missing documentation, some missing '
                  'descriptions, or methods whose @return tags don\'t have a '
                  'matching return statement.'),
            action='append',
            nargs='*',
            metavar="filename")

        parser.add_argument(
            '--error_trace',
            help='show error exceptions.',
            action='store_true')

        parser.add_argument(
            '--closurized_namespaces',
            help=('namespace prefixes, used for testing of'
                  'goog.provide/require'),
            action='append',
            nargs='*',
            metavar="prefix")

        parser.add_argument(
            '--ignored_extra_namespaces',
            help=('Fully qualified namespaces that should be not be reported '
                  'as extra by the linter.'),
            action='append',
            nargs='*',
            metavar="namespace")

        parser.add_argument(
            '--custom_jsdoc_tags',
            help=('extra jsdoc tags to allow'),
            action='append',
            nargs='*',
            metavar="tagname")

        parser.add_argument(
            '--dot_on_next_line',
            help=('Require dots to be'
                  'placed on the next line for wrapped expressions'),
            action='store_true')

        parser.add_argument(
            '--check_trailing_comma',
            help=('check trailing commas '
                  '(ES3, not needed from ES5 onwards)'),
            action='store_true')

        parser.add_argument(
            '--debug_indentation',
            help='print debugging information for indentation',
            action='store_true')

        # Comment - watch this one, backwards internally than before
        parser.add_argument(
            '--jsdoc',
            help='disable reporting errors for missing JsDoc.',
            action='store_true')

        # Comment - this should change to named errors
        parser.add_argument(
            '--disable',
            help=('Disable specific error. Usage Ex.: gjslint --disable 1 '
                  '0011 foo.js.'),
            action='append',
            nargs='*',
            metavar='error_num')

        # Comment - old version checked for minimum of N=1,
        # so maybe check for negative later
        parser.add_argument(
            '--max_line_length',
            type=int,
            help=('Maximum line length allowed '
                  'without warning (default 80).'),
            metavar='N',
            default=80)

        parser.add_argument(
            '--dry_run',
            help='(fixjscodestyle) do not modify the file, only print it.',
            action='store_true')

        # Don't forget everything in error_check.py
        self.args = parser.parse_args()

        # Emacs sets the environment variable INSIDE_EMACS in the subshell.
        # Request Unix mode as emacs will expect output to be in Unix format
        # for integration.
        # See https://www.gnu.org/software/emacs/manual/html_node/emacs/
        # Interactive-Shell.html

        if 'INSIDE_EMACS' in os.environ:
            self.args.unix_mode = True

    def check(self):
        """Check the JavaScript files for style."""
        if self.args.time:
            start_time = time.time()
        suffixes = ['.js']
        if self.args.additional_extensions:
            suffixes += ['.%s' % ext for ext in self.args.additional_extensions]
        if self.args.check_html:
            suffixes += ['.html', '.htm']


def main():
    """Used when called as a command line script."""
    style_checker = JsCodeStyle()
    style_checker.check()


if __name__ == '__main__':
    main()
