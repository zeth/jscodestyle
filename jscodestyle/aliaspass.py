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

"""Pass that scans for goog.scope aliases and lint/usage errors."""

from jscodestyle.ecmametadatapass import EcmaContext
from jscodestyle import errors
from jscodestyle.javascripttokens import JavaScriptTokenType
from jscodestyle import scopeutil
from jscodestyle import tokenutil
from jscodestyle.common import error


def _get_alias_for_identifier(identifier, alias_map):
    """Returns the aliased_symbol name for an identifier.

    Example usage:
      >>> alias_map = {'MyClass': 'goog.foo.MyClass'}
      >>> _get_alias_for_identifier('MyClass.prototype.action', alias_map)
      'goog.foo.MyClass.prototype.action'

      >>> _get_alias_for_identifier('MyClass.prototype.action', {})
      None

    Args:
      identifier: The identifier.
      alias_map: A dictionary mapping a symbol to an alias.

    Returns:
      The aliased symbol name or None if not found.
    """
    namespace = identifier.split('.', 1)[0]
    aliased_symbol = alias_map.get(namespace)
    if aliased_symbol:
        return aliased_symbol + identifier[len(namespace):]


def _set_type_alias(js_type, alias_map):
    """Updates the alias for identifiers in a type.

    Args:
      js_type: A typeannotation.TypeAnnotation instance.
      alias_map: A dictionary mapping a symbol to an alias.
    """
    aliased_symbol = _get_alias_for_identifier(js_type.identifier, alias_map)
    if aliased_symbol:
        js_type.alias = aliased_symbol
    for sub_type in js_type.IterTypes():
        _set_type_alias(sub_type, alias_map)


class AliasPass(object):
    """Pass to identify goog.scope() usages.

    Identifies goog.scope() usages and finds lint/usage errors.  Notes any
    aliases of symbols in Closurized namespaces (that is, reassignments
    such as "var MyClass = goog.foo.MyClass;") and annotates identifiers
    when they're using an alias (so they may be expanded to the full symbol
    later -- that "MyClass.prototype.action" refers to
    "goog.foo.MyClass.prototype.action" when expanded.).
    """

    def __init__(self, closurized_namespaces=None, error_handler=None):
        """Creates a new pass.

        Args:
          closurized_namespaces: A set of Closurized namespaces (e.g. 'goog').
          error_handler: An error handler to report lint errors to.
        """

        self._error_handler = error_handler

        # If we have namespaces, freeze the set.
        if closurized_namespaces:
            closurized_namespaces = frozenset(closurized_namespaces)

        self._closurized_namespaces = closurized_namespaces

    def process(self, start_token):
        """Runs the pass on a token stream.

        Args:
          start_token: The first token in the stream.
        """

        if start_token is None:
            return

        self._check_goog_scope_calls(start_token)

        # If we have closurized namespaces, identify aliased identifiers.
        if self._closurized_namespaces:
            context = start_token.metadata.context
            root_context = context.GetRoot()
            self._process_root_context(root_context)

    def _check_goog_scope_calls(self, start_token):
        """Check goog.scope calls for lint/usage errors."""

        def is_scope_token(token):
            """Returns True if the token is a scope token."""
            return (token.type is
                    JavaScriptTokenType.IDENTIFIER
                    and token.string == 'goog.scope')

        # Find all the goog.scope tokens in the file
        scope_tokens = [t for t in start_token if is_scope_token(t)]

        for token in scope_tokens:
            scope_context = token.metadata.context

            if not (scope_context.type ==
                    EcmaContext.STATEMENT and
                    scope_context.parent.type ==
                    EcmaContext.ROOT):
                self._maybe_report_error(
                    error.Error(errors.INVALID_USE_OF_GOOG_SCOPE,
                                'goog.scope call not in global scope', token))

        # There should be only one goog.scope reference.  Register errors for
        # every instance after the first.
        for token in scope_tokens[1:]:
            self._maybe_report_error(
                error.Error(errors.EXTRA_GOOG_SCOPE_USAGE,
                            'More than one goog.scope call in file.', token))

    def _maybe_report_error(self, err):
        """Report an error to the handler (if registered)."""
        if self._error_handler:
            self._error_handler.handle_error(err)

    @classmethod
    def _yield_all_contexts(cls, context):
        """Yields all contexts that are contained by the given context."""
        yield context
        for child_context in context.children:
            for descendent_child in cls._yield_all_contexts(child_context):
                yield descendent_child

    @staticmethod
    def _is_token_in_parent_block(token, parent_block):
        """Determines whether the given token is contained by the given block.

        Args:
          token: A token
          parent_block: An EcmaContext.

        Returns:
          Whether the token is in a context that is or is a child of the given
          parent_block context.
        """
        context = token.metadata.context

        while context:
            if context is parent_block:
                return True
            context = context.parent

        return False

    def _process_child(self, child):
        """Process a single statement_child."""
        match = scopeutil.MatchModuleAlias(child)
        if match:
            # goog.require aliases cannot use further
            # aliases, the symbol is the second part
            # of match, directly.
            symbol = match[1]
            if scopeutil.IsInClosurizedNamespace(
                    symbol,
                    self._closurized_namespaces):
                return match[0], symbol
        return None, None

    def _process_root_context(self, root_context):
        """Processes all goog.scope blocks under the root context."""

        assert root_context.type is EcmaContext.ROOT

        # Process aliases in statements in the root scope for goog.module-style
        # aliases.
        global_alias_map = {}
        for context in root_context.children:
            if context.type == EcmaContext.STATEMENT:
                for statement_child in context.children:
                    if statement_child.type == EcmaContext.VAR:
                        match, symbol = self._process_child(statement_child)
                        if match:
                            global_alias_map[match] = symbol

        # Process each block to find aliases.
        for context in root_context.children:
            self._process_block(context, global_alias_map)

    def _process_block(self, context, global_alias_map):
        """Scans a goog.scope block to find aliases and mark alias tokens."""
        alias_map = global_alias_map.copy()

        # Iterate over every token in the context. Each token points
        # to one context, but multiple tokens may point to the same
        # context. We only want to check each context once, so keep
        # track of those we've seen.
        seen_contexts = set()
        token = context.start_token
        while token and self._is_token_in_parent_block(token, context):
            token_context = token.metadata.context if token.metadata else None

            # Check to see if this token is an alias.
            if token_context and token_context not in seen_contexts:
                seen_contexts.add(token_context)

                # If this is a alias statement in the goog.scope block.
                if (token_context.type == EcmaContext.VAR and
                        scopeutil.IsGoogScopeBlock(
                            token_context.parent.parent)):
                    match = scopeutil.MatchAlias(token_context)

                    # If this is an alias, remember it in the map.
                    if match:
                        alias, symbol = match
                        symbol = _get_alias_for_identifier(
                            symbol,
                            alias_map) or symbol
                        if scopeutil.IsInClosurizedNamespace(
                                symbol,
                                self._closurized_namespaces):
                            alias_map[alias] = symbol

            # If this token is an identifier that matches an alias,
            # mark the token as an alias to the original symbol.
            if (token.type is JavaScriptTokenType.SIMPLE_LVALUE or
                    token.type is JavaScriptTokenType.IDENTIFIER):
                identifier = tokenutil.GetIdentifierForToken(token)
                if identifier:
                    aliased_symbol = _get_alias_for_identifier(
                        identifier, alias_map)
                    if aliased_symbol:
                        token.metadata.aliased_symbol = aliased_symbol

            elif token.type == JavaScriptTokenType.DOC_FLAG:
                flag = token.attached_object
                if flag and flag.HasType() and flag.jstype:
                    _set_type_alias(flag.jstype, alias_map)

            token = token.next  # Get next token
