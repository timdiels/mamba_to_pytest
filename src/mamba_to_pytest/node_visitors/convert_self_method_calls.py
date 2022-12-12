from __future__ import annotations

import dataclasses
import re

from mamba_to_pytest import nodes
from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.base import NodeVisitor


_MethodScope = frozenset[nodes.Method]
_SELF_PARAM_PATTERN = re.compile(r'(\W)self(\W)')
_FIXTURE_NAME = TestScope.METHOD.fixture_name  # methods only appear in method scoped fixtures


class _ConvertSelfMethodCalls(NodeVisitor):
    def __init__(self):
        self._method_scopes: list[_MethodScope] = [frozenset()]
        self._current_scope: TestScope | None = None

    def visit_root(self, node: nodes.RootNode) -> nodes.RootNode:
        return self._replace_children(node)

    def visit_test_context(self, node: nodes.TestContext) -> nodes.TestContext:
        methods = node.method_fixture and node.method_fixture.methods
        if methods:
            self._method_scopes.append(self._method_scopes[-1] | frozenset(methods))
        node = self._replace_children(node)
        if methods:
            self._method_scopes.pop()
        return node

    def visit_fixture(self, node: nodes.Fixture) -> nodes.Fixture:
        return self._replace_children(node)

    def visit_test_setup(self, node: nodes.TestSetup) -> nodes.TestSetup:
        return self._replace_with_scope(node)

    def visit_test_teardown(self, node: nodes.TestTeardown) -> nodes.TestTeardown:
        return self._replace_with_scope(node)

    def visit_method(self, node: nodes.Method) -> nodes.Method:
        node = self._replace_children(node)
        fixture_name = TestScope.METHOD.fixture_name
        return dataclasses.replace(node, tail=_SELF_PARAM_PATTERN.sub(rf'\1{fixture_name}\2', node.tail))

    def visit_test(self, node: nodes.Test) -> nodes.Test:
        return self._replace_children(node)

    def visit_block_of_code(self, node: nodes.BlockOfCode) -> nodes.BlockOfCode:
        if self._current_scope:
            fixture_name = self._current_scope.fixture_name
        else:
            fixture_name = TestScope.METHOD.fixture_name

        body = node.body
        for method in self._method_scopes[-1]:
            method_call_start = rf'(\W)self(.{method.name}\()'
            body = re.sub(rf'{method_call_start}\s*([^)])', rf'\1{fixture_name}\2{fixture_name}, \3', body)
            body = re.sub(rf'{method_call_start}\s*\)', rf'\1{fixture_name}\2{fixture_name})', body)
        return dataclasses.replace(node, body=body)

    def _replace_with_scope(self, node: nodes.TestSetup | nodes.TestTeardown):
        self._current_scope = node.scope
        node = self._replace_children(node)
        self._current_scope = None
        return node


def convert_self_method_calls(root: nodes.RootNode) -> nodes.RootNode:
    return root.accept(_ConvertSelfMethodCalls())
