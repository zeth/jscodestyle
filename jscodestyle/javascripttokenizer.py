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

"""Regular expression based JavaScript parsing classes."""

import copy
import re

from jscodestyle.javascripttokens import JavaScriptTokenType as Type
from jscodestyle.javascripttokens import JavaScriptToken as Token
from jscodestyle.common.matcher import Matcher
from jscodestyle.common import tokenizer


class JavaScriptModes(object):
    """Enumeration of the different matcher modes used for JavaScript."""
    TEXT_MODE = 'text'
    SINGLE_QUOTE_STRING_MODE = 'single_quote_string'
    DOUBLE_QUOTE_STRING_MODE = 'double_quote_string'
    TEMPLATE_STRING_MODE = 'template_string'
    BLOCK_COMMENT_MODE = 'block_comment'
    DOC_COMMENT_MODE = 'doc_comment'
    DOC_COMMENT_LEX_SPACES_MODE = 'doc_comment_spaces'
    LINE_COMMENT_MODE = 'line_comment'
    PARAMETER_MODE = 'parameter'
    FUNCTION_MODE = 'function'


class JavaScriptTokenizer(tokenizer.Tokenizer):
    """JavaScript tokenizer.

    Convert JavaScript code in to an array of tokens.
    """

    # Useful patterns for JavaScript parsing.
    IDENTIFIER_CHAR = r'A-Za-z0-9_$'

    # Number patterns based on:
    # http://www.mozilla.org/js/language/js20-2000-07/formal/lexer-grammar.html
    MANTISSA = r"""
               (\d+(?!\.)) |                # Matches '10'
               (\d+\.(?!\d)) |              # Matches '10.'
               (\d*\.\d+)                   # Matches '.5' or '10.5'
               """
    DECIMAL_LITERAL = r'(%s)([eE][-+]?\d+)?' % MANTISSA
    HEX_LITERAL = r'0[xX][0-9a-fA-F]+'
    NUMBER = re.compile(r"""
                        ((%s)|(%s))
                        """ % (HEX_LITERAL, DECIMAL_LITERAL), re.VERBOSE)

    # Strings come in three parts - first we match the start of the string, then
    # the contents, then the end.  The contents consist of any character except a
    # backslash or end of string, or a backslash followed by any character, or a
    # backslash followed by end of line to support correct parsing of multi-line
    # strings.
    SINGLE_QUOTE = re.compile(r"'")
    SINGLE_QUOTE_TEXT = re.compile(r"([^'\\]|\\(.|$))+")
    DOUBLE_QUOTE = re.compile(r'"')
    DOUBLE_QUOTE_TEXT = re.compile(r'([^"\\]|\\(.|$))+')
    # Template strings are different from normal strings in that they do not
    # require escaping of end of lines in order to be multi-line.
    TEMPLATE_QUOTE = re.compile(r'`')
    TEMPLATE_QUOTE_TEXT = re.compile(r'([^`]|$)+')

    START_SINGLE_LINE_COMMENT = re.compile(r'//')
    END_OF_LINE_SINGLE_LINE_COMMENT = re.compile(r'//$')

    START_DOC_COMMENT = re.compile(r'/\*\*')
    START_BLOCK_COMMENT = re.compile(r'/\*')
    END_BLOCK_COMMENT = re.compile(r'\*/')
    BLOCK_COMMENT_TEXT = re.compile(r'([^*]|\*(?!/))+')

    # Comment text is anything that we are not going to parse into another special
    # token like (inline) flags or end comments. Complicated regex to match
    # most normal characters, and '*', '{', '}', and '@' when we are sure that
    # it is safe. Expression [^*{\s]@ must come first, or the other options will
    # match everything before @, and we won't match @'s that aren't part of flags
    # like in email addresses in the @author tag.
    DOC_COMMENT_TEXT = re.compile(r'([^*{}\s]@|[^*{}@]|\*(?!/))+')
    DOC_COMMENT_NO_SPACES_TEXT = re.compile(r'([^*{}\s]@|[^*{}@\s]|\*(?!/))+')
    # Match anything that is allowed in a type definition, except for tokens
    # needed to parse it (and the lookahead assertion for "*/").
    DOC_COMMENT_TYPE_TEXT = re.compile(r'([^*|!?=<>(){}:,\s]|\*(?!/))+')

    # Match the prefix ' * ' that starts every line of jsdoc. Want to include
    # spaces after the '*', but nothing else that occurs after a '*', and don't
    # want to match the '*' in '*/'.
    DOC_PREFIX = re.compile(r'\s*\*(\s+|(?!/))')

    START_BLOCK = re.compile('{')
    END_BLOCK = re.compile('}')

    REGEX_CHARACTER_CLASS = r"""
                            \[               # Opening bracket
                            ([^\]\\]|\\.)*   # Anything but a ] or \,
                                             # or a backslash followed by anything
                            \]               # Closing bracket
                            """
    # We ensure the regex is followed by one of the above tokens to avoid
    # incorrectly parsing something like x / y / z as x REGEX(/ y /) z
    POST_REGEX_LIST = [
        ';', ',', r'\.', r'\)', r'\]', '$', r'\/\/', r'\/\*', ':', '}']

    REGEX = re.compile(r"""
                       /                      # opening slash
                       (?!\*)                 # not the start of a comment
                       (\\.|[^\[\/\\]|(%s))*  # a backslash followed by anything,
                                              # or anything but a / or [ or \,
                                              # or a character class
                       /                      # closing slash
                       [gimsx]*               # optional modifiers
                       (?=\s*(%s))
                       """ % (REGEX_CHARACTER_CLASS, '|'.join(POST_REGEX_LIST)),
                       re.VERBOSE)

    ANYTHING = re.compile(r'.*')
    PARAMETERS = re.compile(r'[^\)]+')
    CLOSING_PAREN_WITH_SPACE = re.compile(r'\)\s*')

    FUNCTION_DECLARATION = re.compile(r'\bfunction\b')

    OPENING_PAREN = re.compile(r'\(')
    CLOSING_PAREN = re.compile(r'\)')

    OPENING_BRACKET = re.compile(r'\[')
    CLOSING_BRACKET = re.compile(r'\]')

    # We omit these JS keywords from the list:
    #   function - covered by FUNCTION_DECLARATION.
    #   delete, in, instanceof, new, typeof - included as operators.
    #   this - included in identifiers.
    #   null, undefined - not included, should go in some "special constant" list.
    KEYWORD_LIST = [
        'break',
        'case',
        'catch',
        'continue',
        'default',
        'do',
        'else',
        'finally',
        'for',
        'if',
        'return',
        'switch',
        'throw',
        'try',
        'var',
        'while',
        'with',
    ]

    # List of regular expressions to match as operators.  Some notes: for our
    # purposes, the comma behaves similarly enough to a normal operator that we
    # include it here.  r'\bin\b' actually matches 'in' surrounded by boundary
    # characters - this may not match some very esoteric uses of the in operator.
    # Operators that are subsets of larger operators must come later in this list
    # for proper matching, e.g., '>>' must come AFTER '>>>'.
    OPERATOR_LIST = [
        ',',
        r'\+\+',
        '===',
        '!==',
        '>>>=',
        '>>>',
        '==',
        '>=',
        '<=',
        '!=',
        '<<=',
        '>>=',
        '<<',
        '>>',
        '=>',
        '>',
        '<',
        r'\+=',
        r'\+',
        '--',
        r'\^=',
        '-=',
        '-',
        '/=',
        '/',
        r'\*=',
        r'\*',
        '%=',
        '%',
        '&&',
        r'\|\|',
        '&=',
        '&',
        r'\|=',
        r'\|',
        '=',
        '!',
        ':',
        r'\?',
        r'\^',
        r'\bdelete\b',
        r'\bin\b',
        r'\binstanceof\b',
        r'\bnew\b',
        r'\btypeof\b',
        r'\bvoid\b',
        r'\.',
    ]
    OPERATOR = re.compile('|'.join(OPERATOR_LIST))

    WHITESPACE = re.compile(r'\s+')
    SEMICOLON = re.compile(r';')
    # Technically JavaScript identifiers can't contain '.', but we treat a set of
    # nested identifiers as a single identifier, except for trailing dots.
    NESTED_IDENTIFIER = r'[a-zA-Z_$]([%s]|\.[a-zA-Z_$])*' % IDENTIFIER_CHAR
    IDENTIFIER = re.compile(NESTED_IDENTIFIER)

    SIMPLE_LVALUE = re.compile(r"""
                               (?P<identifier>%s)      # a valid identifier
                               (?=\s*                  # optional whitespace
                               \=                      # look ahead to equal sign
                               (?!=))                  # not follwed by equal
                               """ % NESTED_IDENTIFIER, re.VERBOSE)

    # A doc flag is a @ sign followed by non-space characters that appears at the
    # beginning of the line, after whitespace, or after a '{'.  The look-behind
    # check is necessary to not match someone@google.com as a flag.
    DOC_FLAG = re.compile(r'(^|(?<=\s))@(?P<name>[a-zA-Z]+)')
    # To properly parse parameter names and complex doctypes containing
    # whitespace, we need to tokenize whitespace into a token after certain
    # doctags. All statetracker.HAS_TYPE that are not listed here must not contain
    # any whitespace in their types.
    DOC_FLAG_LEX_SPACES = re.compile(
        r'(^|(?<=\s))@(?P<name>%s)\b' %
        '|'.join([
            'const',
            'enum',
            'export',
            'extends',
            'final',
            'implements',
            'package',
            'param',
            'private',
            'protected',
            'public',
            'return',
            'type',
            'typedef'
        ]))

    DOC_INLINE_FLAG = re.compile(r'(?<={)@(?P<name>[a-zA-Z]+)')

    DOC_TYPE_BLOCK_START = re.compile(r'[<(]')
    DOC_TYPE_BLOCK_END = re.compile(r'[>)]')
    DOC_TYPE_MODIFIERS = re.compile(r'[!?|,:=]')

    # Star followed by non-slash, i.e a star that does not end a comment.
    # This is used for TYPE_GROUP below.
    SAFE_STAR = r'(\*(?!/))'

    COMMON_DOC_MATCHERS = [
        # Find the end of the comment.
        Matcher(END_BLOCK_COMMENT, Type.END_DOC_COMMENT,
                JavaScriptModes.TEXT_MODE),

        # Tokenize documented flags like @private.
        Matcher(DOC_INLINE_FLAG, Type.DOC_INLINE_FLAG),
        Matcher(DOC_FLAG_LEX_SPACES, Type.DOC_FLAG,
                JavaScriptModes.DOC_COMMENT_LEX_SPACES_MODE),

        # Encountering a doc flag should leave lex spaces mode.
        Matcher(DOC_FLAG, Type.DOC_FLAG, JavaScriptModes.DOC_COMMENT_MODE),

        # Tokenize braces so we can find types.
        Matcher(START_BLOCK, Type.DOC_START_BRACE),
        Matcher(END_BLOCK, Type.DOC_END_BRACE),

        # And some more to parse types.
        Matcher(DOC_TYPE_BLOCK_START, Type.DOC_TYPE_START_BLOCK),
        Matcher(DOC_TYPE_BLOCK_END, Type.DOC_TYPE_END_BLOCK),

        Matcher(DOC_TYPE_MODIFIERS, Type.DOC_TYPE_MODIFIER),
        Matcher(DOC_COMMENT_TYPE_TEXT, Type.COMMENT),

        Matcher(DOC_PREFIX, Type.DOC_PREFIX, None, True)]

    # When text is not matched, it is given this default type based on mode.
    # If unspecified in this map, the default default is Type.NORMAL.
    JAVASCRIPT_DEFAULT_TYPES = {
        JavaScriptModes.DOC_COMMENT_MODE: Type.COMMENT,
        JavaScriptModes.DOC_COMMENT_LEX_SPACES_MODE: Type.COMMENT
    }

    @classmethod
    def build_matchers(cls):
        """Builds the token matcher group.

        The token matcher groups work as follows: it is a list of Matcher objects.
        The matchers will be tried in this order, and the first to match will be
        returned.  Hence the order is important because the matchers that come first
        overrule the matchers that come later.

        Returns:
          The completed token matcher group.
        """
        # Match a keyword string followed by a non-identifier character in order to
        # not match something like doSomething as do + Something.
        keyword = re.compile('(%s)((?=[^%s])|$)' % (
            '|'.join(cls.KEYWORD_LIST), cls.IDENTIFIER_CHAR))
        return {

            # Matchers for basic text mode.
            JavaScriptModes.TEXT_MODE: [
                # Check a big group - strings, starting comments, and regexes - all
                # of which could be intertwined.  'string with /regex/',
                # /regex with 'string'/, /* comment with /regex/ and string */ (and
                # so on)
                Matcher(cls.START_DOC_COMMENT, Type.START_DOC_COMMENT,
                        JavaScriptModes.DOC_COMMENT_MODE),
                Matcher(cls.START_BLOCK_COMMENT, Type.START_BLOCK_COMMENT,
                        JavaScriptModes.BLOCK_COMMENT_MODE),
                Matcher(cls.END_OF_LINE_SINGLE_LINE_COMMENT,
                        Type.START_SINGLE_LINE_COMMENT),
                Matcher(cls.START_SINGLE_LINE_COMMENT,
                        Type.START_SINGLE_LINE_COMMENT,
                        JavaScriptModes.LINE_COMMENT_MODE),
                Matcher(cls.SINGLE_QUOTE, Type.SINGLE_QUOTE_STRING_START,
                        JavaScriptModes.SINGLE_QUOTE_STRING_MODE),
                Matcher(cls.DOUBLE_QUOTE, Type.DOUBLE_QUOTE_STRING_START,
                        JavaScriptModes.DOUBLE_QUOTE_STRING_MODE),
                Matcher(cls.TEMPLATE_QUOTE, Type.TEMPLATE_STRING_START,
                        JavaScriptModes.TEMPLATE_STRING_MODE),
                Matcher(cls.REGEX, Type.REGEX),

                # Next we check for start blocks appearing outside any of the items
                # above.
                Matcher(cls.START_BLOCK, Type.START_BLOCK),
                Matcher(cls.END_BLOCK, Type.END_BLOCK),

                # Then we search for function declarations.
                Matcher(cls.FUNCTION_DECLARATION, Type.FUNCTION_DECLARATION,
                        JavaScriptModes.FUNCTION_MODE),

                # Next, we convert non-function related parens to tokens.
                Matcher(cls.OPENING_PAREN, Type.START_PAREN),
                Matcher(cls.CLOSING_PAREN, Type.END_PAREN),

                # Next, we convert brackets to tokens.
                Matcher(cls.OPENING_BRACKET, Type.START_BRACKET),
                Matcher(cls.CLOSING_BRACKET, Type.END_BRACKET),

                # Find numbers.  This has to happen before operators because
                # scientific notation numbers can have + and - in them.
                Matcher(cls.NUMBER, Type.NUMBER),

                # Find operators and simple assignments
                Matcher(cls.SIMPLE_LVALUE, Type.SIMPLE_LVALUE),
                Matcher(cls.OPERATOR, Type.OPERATOR),

                # Find key words and whitespace.
                Matcher(keyword, Type.KEYWORD),
                Matcher(cls.WHITESPACE, Type.WHITESPACE),

                # Find identifiers.
                Matcher(cls.IDENTIFIER, Type.IDENTIFIER),

                # Finally, we convert semicolons to tokens.
                Matcher(cls.SEMICOLON, Type.SEMICOLON)],

            # Matchers for single quote strings.
            JavaScriptModes.SINGLE_QUOTE_STRING_MODE: [
                Matcher(cls.SINGLE_QUOTE_TEXT, Type.STRING_TEXT),
                Matcher(cls.SINGLE_QUOTE, Type.SINGLE_QUOTE_STRING_END,
                        JavaScriptModes.TEXT_MODE)],

            # Matchers for double quote strings.
            JavaScriptModes.DOUBLE_QUOTE_STRING_MODE: [
                Matcher(cls.DOUBLE_QUOTE_TEXT, Type.STRING_TEXT),
                Matcher(cls.DOUBLE_QUOTE, Type.DOUBLE_QUOTE_STRING_END,
                        JavaScriptModes.TEXT_MODE)],

            # Matchers for template strings.
            JavaScriptModes.TEMPLATE_STRING_MODE: [
                Matcher(cls.TEMPLATE_QUOTE_TEXT, Type.STRING_TEXT),
                Matcher(cls.TEMPLATE_QUOTE, Type.TEMPLATE_STRING_END,
                        JavaScriptModes.TEXT_MODE)],

            # Matchers for block comments.
            JavaScriptModes.BLOCK_COMMENT_MODE: [
                # First we check for exiting a block comment.
                Matcher(cls.END_BLOCK_COMMENT, Type.END_BLOCK_COMMENT,
                        JavaScriptModes.TEXT_MODE),

                # Match non-comment-ending text..
                Matcher(cls.BLOCK_COMMENT_TEXT, Type.COMMENT)],

            # Matchers for doc comments.
            JavaScriptModes.DOC_COMMENT_MODE: cls.COMMON_DOC_MATCHERS + [
                Matcher(cls.DOC_COMMENT_TEXT, Type.COMMENT)],

            JavaScriptModes.DOC_COMMENT_LEX_SPACES_MODE: cls.COMMON_DOC_MATCHERS + [
                Matcher(cls.WHITESPACE, Type.COMMENT),
                Matcher(cls.DOC_COMMENT_NO_SPACES_TEXT, Type.COMMENT)],

            # Matchers for single line comments.
            JavaScriptModes.LINE_COMMENT_MODE: [
                # We greedy match until the end of the line in line comment mode.
                Matcher(cls.ANYTHING, Type.COMMENT, JavaScriptModes.TEXT_MODE)],

            # Matchers for code after the function keyword.
            JavaScriptModes.FUNCTION_MODE: [
                # Must match open paren before anything else and move into parameter
                # mode, otherwise everything inside the parameter list is parsed
                # incorrectly.
                Matcher(cls.OPENING_PAREN, Type.START_PARAMETERS,
                        JavaScriptModes.PARAMETER_MODE),
                Matcher(cls.WHITESPACE, Type.WHITESPACE),
                Matcher(cls.IDENTIFIER, Type.FUNCTION_NAME)],

            # Matchers for function parameters
            JavaScriptModes.PARAMETER_MODE: [
                # When in function parameter mode, a closing paren is treated
                # specially. Everything else is treated as lines of parameters.
                Matcher(cls.CLOSING_PAREN_WITH_SPACE, Type.END_PARAMETERS,
                        JavaScriptModes.TEXT_MODE),
                Matcher(cls.PARAMETERS, Type.PARAMETERS,
                        JavaScriptModes.PARAMETER_MODE)]}

    def __init__(self, parse_js_doc=True):
        """Create a tokenizer object.

        Args:
          parse_js_doc: Whether to do detailed parsing of javascript doc comments,
              or simply treat them as normal comments.  Defaults to parsing JsDoc.
        """
        matchers = self.build_matchers()
        if not parse_js_doc:
            # Make a copy so the original doesn't get modified.
            matchers = copy.deepcopy(matchers)
            matchers[JavaScriptModes.DOC_COMMENT_MODE] = matchers[
                JavaScriptModes.BLOCK_COMMENT_MODE]

        tokenizer.Tokenizer.__init__(self,
                                     JavaScriptModes.TEXT_MODE,
                                     matchers,
                                     self.JAVASCRIPT_DEFAULT_TYPES)

    def _CreateToken(self, string, token_type, line, line_number, values=None):
        """Creates a new JavaScriptToken object.

        Args:
          string: The string of input the token contains.
          token_type: The type of token.
          line: The text of the line this token is in.
          line_number: The line number of the token.
          values: A dict of named values within the token.  For instance, a
            function declaration may have a value called 'name' which captures the
            name of the function.
        """
        return Token(string, token_type, line,
                     line_number, values, line_number)
