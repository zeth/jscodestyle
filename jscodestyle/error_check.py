#!/usr/bin/env python
#
# Copyright 2018 The JsCodeStyle Authors.
# Copyright 2011 The Closure Linter Authors. All Rights Reserved.
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


"""Specific JSLint errors checker."""


class Rule(object):
    """Different rules to check."""

    # Documentations for specific rules goes in flag definition.
    BLANK_LINES_AT_TOP_LEVEL = 'blank_lines_at_top_level'
    INDENTATION = 'indentation'
    WELL_FORMED_AUTHOR = 'well_formed_author'
    NO_BRACES_AROUND_INHERIT_DOC = 'no_braces_around_inherit_doc'
    BRACES_AROUND_TYPE = 'braces_around_type'
    OPTIONAL_TYPE_MARKER = 'optional_type_marker'
    VARIABLE_ARG_MARKER = 'variable_arg_marker'
    UNUSED_PRIVATE_MEMBERS = 'unused_private_members'
    UNUSED_LOCAL_VARIABLES = 'unused_local_variables'

    # Rule to raise all known errors.
    ALL = 'all'

    # All rules that are to be checked when using the strict flag
    # E.g. the rules that are specific to the stricter Closure style.
    CLOSURE_RULES = frozenset([BLANK_LINES_AT_TOP_LEVEL,
                               INDENTATION,
                               WELL_FORMED_AUTHOR,
                               NO_BRACES_AROUND_INHERIT_DOC,
                               BRACES_AROUND_TYPE,
                               OPTIONAL_TYPE_MARKER,
                               VARIABLE_ARG_MARKER])


STRICT_DOC = ('Whether to validate against the stricter Closure style. '
              'This includes ' + (', '.join(Rule.CLOSURE_RULES)) + '.')

JSLINT_ERROR_DOC = ('List of specific lint errors to check. '
                    'Here is a list of accepted values:\n'
                    ' - ' + Rule.ALL + ': enables all following errors.\n'
                    ' - ' + Rule.BLANK_LINES_AT_TOP_LEVEL + ': validates'
                    'number of blank lines between blocks at top level.\n'
                    ' - ' + Rule.INDENTATION + ': checks correct '
                    'indentation of code.\n'
                    ' - ' + Rule.WELL_FORMED_AUTHOR + ': validates the '
                    '@author JsDoc tags.\n'
                    ' - ' + Rule.NO_BRACES_AROUND_INHERIT_DOC + ': '
                    'forbids braces around @inheritdoc JsDoc tags.\n'
                    ' - ' + Rule.BRACES_AROUND_TYPE + ': enforces braces '
                    'around types in JsDoc tags.\n'
                    ' - ' + Rule.OPTIONAL_TYPE_MARKER + ': checks '
                    'correct use of optional marker = in param types.\n'
                    ' - ' + Rule.UNUSED_PRIVATE_MEMBERS + ': checks for '
                    'unused private variables.\n'
                    ' - ' + Rule.UNUSED_LOCAL_VARIABLES + ': checks for '
                    'unused local variables.\n')
