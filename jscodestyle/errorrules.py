#!/usr/bin/env python
#
# Copyright 2018 The JsCodeStyle Authors.
# Copyright 2010 The Closure Linter Authors. All Rights Reserved.
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

"""Linter error rules class for Closure Linter."""


from jscodestyle import errors



disabled_error_nums = None


# This should just be a method of LintRulesBase

def ShouldReportError(jsdoc, disable, error):
    """Whether the given error should be reported.

    Returns:
      True for all errors except missing documentation errors and disabled
      errors.  For missing documentation, it returns the value of the
      jsdoc flag.
    """
    global disabled_error_nums
    if disabled_error_nums is None:
        disabled_error_nums = []
        if disable:
            for error_str in disable:
                error_num = 0
                try:
                    error_num = int(error_str)
                except ValueError:
                    pass
                disabled_error_nums.append(error_num)

    return ((jsdoc or error not in (
        errors.MISSING_PARAMETER_DOCUMENTATION,
        errors.MISSING_RETURN_DOCUMENTATION,
        errors.MISSING_MEMBER_DOCUMENTATION,
        errors.MISSING_PRIVATE,
        errors.MISSING_JSDOC_TAG_THIS)) and
            (not disable or error not in disabled_error_nums))
