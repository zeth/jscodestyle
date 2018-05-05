#!/usr/bin/env python
#
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

"""Core methods for checking JS files for common style guide violations."""

from jscodestyle import aliaspass
from jscodestyle import checkerbase
from jscodestyle import closurizednamespacesinfo
from jscodestyle import javascriptlintrules


class JavaScriptStyleChecker(checkerbase.CheckerBase):
    """Checker that applies JavaScriptLintRules."""

    def __init__(self,
                 state_tracker,
                 error_handler,
                 closurized_namespaces,
                 ignored_extra_namespaces,
                 custom_jsdoc_tags,
                 dot_on_next_line,
                 check_trailing_comma,
                 debug_indentation,
                 jslint_error,
                 strict,
                 max_line_length,
                 limited_doc_checks,
                 is_html,
                 jsdoc,
                 disable):
        """Initialize an JavaScriptStyleChecker object.

        Args:
          state_tracker: State tracker.
          error_handler: Error handler to pass all errors to.
        """
        self.namespaces_info = None
        self._alias_pass = None
        if closurized_namespaces:
            self.namespaces_info = (
                closurizednamespacesinfo.ClosurizedNamespacesInfo(
                    closurized_namespaces,
                    ignored_extra_namespaces))

            self._alias_pass = aliaspass.AliasPass(
                closurized_namespaces, error_handler)

        lint_rules = javascriptlintrules.JavaScriptLintRules(
            self.namespaces_info,
            error_handler,
            custom_jsdoc_tags,
            dot_on_next_line,
            check_trailing_comma,
            debug_indentation,
            jslint_error,
            strict,
            max_line_length,
            limited_doc_checks,
            is_html,
            jsdoc,
            disable)

        super(JavaScriptStyleChecker, self).__init__(
            error_handler,
            lint_rules,
            state_tracker)

    def check(self,
              start_token,
              stop_token=None):
        """Checks a token stream for lint warnings/errors.

        Adds a separate pass for computing dependency information based on
        goog.require and goog.provide statements prior to the main linting pass.

        Args:
          start_token: The first token in the token stream.
          limited_doc_checks: Whether to perform limited checks.
          is_html: Whether this token stream is HTML.
          stop_token: If given, checks should stop at this token.
        """
        self._state_tracker.DocFlagPass(start_token, self._error_handler)

        if self._alias_pass:
            self._alias_pass.process(start_token)

        # To maximize the amount of errors that get reported before a parse error
        # is displayed, don't run the dependency pass if a parse error exists.
        if self.namespaces_info:
            self.namespaces_info.reset()
            self._execute_pass(start_token, self._dependency_pass, stop_token)

        self._execute_pass(start_token, self._lint_pass, stop_token)

        # If we have a stop_token, we didn't end up reading the whole file and,
        # thus, don't call finish to do end-of-file checks.
        if not stop_token:
            self._lint_rules.finish(self._state_tracker)

    def _dependency_pass(self, token):
        """Processes an individual token for dependency information.

        Used to encapsulate the logic needed to process an individual token so that
        it can be passed to _execute_pass.

        Args:
          token: The token to process.
        """
        self.namespaces_info.process_token(token, self._state_tracker)
