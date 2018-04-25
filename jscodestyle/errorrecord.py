#!/usr/bin/env python
# Copyright 2018 The JsCodeStyle Authors.
# Copyright 2012 The Closure Linter Authors. All Rights Reserved.
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


"""A simple, pickle-serializable class to represent a lint error."""


from jscodestyle import errors
from jscodestyle.common import erroroutput
from jscodestyle.common import erroraccumulator
from jscodestyle import runner


class ErrorRecord(object):
    """Record-keeping struct that can be serialized back from a process.

    Attributes:
      path: Path to the file.
      error_string: Error string for the user.
      new_error: Whether this is a "new error" (see errors.NEW_ERRORS).
    """

    def __init__(self, path, error_string, new_error):
        self.path = path
        self.error_string = error_string
        self.new_error = new_error


def make_error_record(path, error, unix_mode=False):
    """Make an error record with correctly formatted error string.

    Errors are not able to be serialized (pickled) over processes because of
    their pointers to the complex token/context graph.  We use an intermediary
    serializable class to pass back just the relevant information.

    Args:
      path: Path of file the error was found in.
      error: An error.Error instance.

    Returns:
      _ErrorRecord instance.
    """
    new_error = error.code in errors.NEW_ERRORS

    if unix_mode:
        error_string = erroroutput.GetUnixErrorOutput(
            path, error, new_error=new_error)
    else:
        error_string = erroroutput.GetErrorOutput(error, new_error=new_error)

    return ErrorRecord(path, error_string, new_error)


def check_path(path,
               unix_mode=False,
               limited_doc_files=None,
               error_trace=None):
    """Check a path and return any errors.

    Args:
      path: paths to check.

    Returns:
      A list of errorrecord.ErrorRecords for any found errors.
    """
    if not limited_doc_files:
        limited_doc_files = []

    error_handler = erroraccumulator.ErrorAccumulator()
    runner.Run(path,
               error_handler,
               limited_doc_files,
               error_trace)

    make_error_fn = lambda err: make_error_record(
        path,
        err,
        unix_mode)
    return map(make_error_fn, error_handler.GetErrors())
