#!/usr/bin/env python
#
# Copyright 2018 The JsCodeStyle Authors.
# Copyright 2008 The Closure Linter Authors. All Rights Reserved.
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

"""Base classes for writing checkers that operate on tokens."""

from jscodestyle import errors
from jscodestyle.common.error import Error


class LintRulesBase(object):
    """Base class for all classes defining the lint rules for a language."""

    def __init__(self,
                 error_handler,
                 limited_doc_checks,
                 is_html,
                 jsdoc,
                 disable):
        """Initializes to prepare to check a file.

        Args:
          checker: Class to report errors to.
          limited_doc_checks: Whether doc checking is relaxed for this file.
          is_html: Whether the file is an HTML file with extracted contents.
          jsdoc: Whether to report errors for missing JsDoc.
          disable: Disable specific error.
        """
        self.error_handler = error_handler
        self._limited_doc_checks = limited_doc_checks
        self._is_html = is_html
        self.jsdoc = jsdoc
        self.disable = disable

    def _handle_error(self, code, message, token, position=None,
                      fix_data=None):
        """Call the handle_error function for the checker we are associated with."""
        if self.should_report_error(code):
            self.error_handler.handle_error(
                Error(code, message, token, position, fix_data))

    def _set_limited_doc_checks(self, limited_doc_checks):
        """Sets whether doc checking is relaxed for this file.

        Args:
          limited_doc_checks: Whether doc checking is relaxed for this file.
        """
        self._limited_doc_checks = limited_doc_checks

    def check_token(self, token, parser_state):
        """Checks a token, given the current parser_state, for warnings and errors.

        Args:
          token: The current token under consideration.
          parser_state: Object that indicates the parser state in the page.

        Raises:
          NotImplementedError: If not overridden.
        """
        raise NotImplementedError

    def finish(self, parser_state):
        """Perform all checks that need to occur after all lines are processed.

        Args:
          parser_state: State of the parser after parsing all tokens

        Raises:
          NotImplementedError: If not overridden.
        """
        raise NotImplementedError

    def should_report_error(self, error):
        """Whether the given error should be reported.

        Returns:
          True for all errors except missing documentation errors and disabled
          errors.  For missing documentation, it returns the value of the
          jsdoc flag.
        """

        disabled_error_nums = []
        if self.disable:
            for error_str in self.disable:
                error_num = 0
                try:
                    error_num = int(error_str)
                except ValueError:
                    pass
                disabled_error_nums.append(error_num)

        return ((self.jsdoc or error not in (
            errors.MISSING_PARAMETER_DOCUMENTATION,
            errors.MISSING_RETURN_DOCUMENTATION,
            errors.MISSING_MEMBER_DOCUMENTATION,
            errors.MISSING_PRIVATE,
            errors.MISSING_JSDOC_TAG_THIS)) and
                (not self.disable or error not in disabled_error_nums))


class CheckerBase(object):
    """This class handles checking a LintRules object against a file."""

    def __init__(self,
                 error_handler,
                 lint_rules,
                 state_tracker):
        """Initialize a checker object.

        Args:
          error_handler: Object that handles errors.
          lint_rules: LintRules object defining lint errors given a token
            and state_tracker object.
          state_tracker: Object that tracks the current state in the token stream.

        """
        self._error_handler = error_handler
        self._lint_rules = lint_rules
        self._state_tracker = state_tracker

        self._has_errors = False

    def handle_error(self, code, message, token, position=None,
                     fix_data=None):
        """Prints out the given error message including a line number.

        Args:
          code: The error code.
          message: The error to print.
          token: The token where the error occurred, or None if it was a file-wide
              issue.
          position: The position of the error, defaults to None.
          fix_data: Metadata used for fixing the error.
        """
        self._has_errors = True
        self._error_handler.handle_error(
            Error(code, message, token, position, fix_data))

    def has_errors(self):
        """Returns true if the style checker has found any errors.

        Returns:
          True if the style checker has found any errors.
        """
        return self._has_errors

    def check(self, start_token, stop_token=None):
        """Checks a token stream, reporting errors to the error reporter.

        Args:
          start_token: First token in token stream.
          limited_doc_checks: Whether doc checking is relaxed for this file.
          is_html: Whether the file being checked is an HTML file with extracted
              contents.
          stop_token: If given, check should stop at this token.
        """

        self._execute_pass(start_token, self._lint_pass, stop_token=stop_token)
        self._lint_rules.finish(self._state_tracker)

    def _lint_pass(self, token):
        """Checks an individual token for lint warnings/errors.

        Used to encapsulate the logic needed to check an individual token so that it
        can be passed to _execute_pass.

        Args:
          token: The token to check.
        """
        self._lint_rules.check_token(token, self._state_tracker)

    def _execute_pass(self, token, pass_function, stop_token=None):
        """Calls the given function for every token in the given token stream.

        As each token is passed to the given function, state is kept up to date and,
        depending on the error_trace flag, errors are either caught and reported, or
        allowed to bubble up so developers can see the full stack trace. If a parse
        error is specified, the pass will proceed as normal until the token causing
        the parse error is reached.

        Args:
          token: The first token in the token stream.
          pass_function: The function to call for each token in the token stream.
          stop_token: The last token to check (if given).

        Raises:
          Exception: If any error occurred while calling the given function.
        """

        self._state_tracker.reset()
        while token:
            # When we are looking at a token and decided to delete the whole line, we
            # will delete all of them in the "HandleToken()" below.  So the current
            # token and subsequent ones may already be deleted here.  The way we
            # delete a token does not wipe out the previous and next pointers of the
            # deleted token.  So we need to check the token itself to make sure it is
            # not deleted.
            if not token.is_deleted:
                # End the pass at the stop token
                if stop_token and token is stop_token:
                    return

                self._state_tracker.HandleToken(
                    token, self._state_tracker.GetLastNonSpaceToken())
                pass_function(token)
                self._state_tracker.handle_after_token(token)

            token = token.next
