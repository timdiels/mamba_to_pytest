from __future__ import annotations

import dataclasses
import typing as t

from mamba_to_pytest import nodes
from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.base import NodeVisitor


class _AddMethodsToFixtures(NodeVisitor):
    def visit_root(self, node: nodes.RootNode) -> nodes.RootNode:
        return self._replace_children(node)

    def visit_test_context(self, node: nodes.TestContext) -> nodes.TestContext:
        node = self._replace_children(node)
        methods, other_children = self._split_children(node.other_children)
        if methods:
            if node.method_fixture:
                fixture_indent = node.method_fixture.indent
                fixture_body_indent = node.method_fixture.body_indent
            else:
                fixture_indent = methods[0].indent
                fixture_body_indent = fixture_indent + 4

            # Indent methods into fixture
            methods = tuple(method.replace_indent(fixture_body_indent) for method in methods)

            if node.method_fixture:
                assert not node.method_fixture.methods
                method_fixture = dataclasses.replace(node.method_fixture, methods=methods)
            else:
                method_fixture = nodes.Fixture(
                    setup=None,
                    teardown=None,
                    methods=methods,
                    indent=fixture_indent,
                    scope=TestScope.METHOD,
                )
                
            return dataclasses.replace(node, method_fixture=method_fixture, other_children=other_children)
        else:
            return node

    @staticmethod
    def _split_children(
            children: t.Iterable[nodes.NodeBase]
    ) -> tuple[tuple[nodes.Method, ...], tuple[nodes.NodeBase, ...]]:
        methods = []
        other_children = []
        for child in children:
            if isinstance(child, nodes.Method):
                methods.append(child)
            else:
                other_children.append(child)
        return tuple(methods), tuple(other_children)

    def visit_test_setup(self, node: nodes.TestSetup) -> nodes.TestSetup:
        raise AssertionError('Does not get called because not touching fixture children')

    def visit_test_teardown(self, node: nodes.TestTeardown) -> nodes.TestTeardown:
        raise AssertionError('Does not get called because not touching fixture children')

    def visit_fixture(self, node: nodes.Fixture) -> nodes.Fixture:
        return node

    def visit_method(self, node: nodes.Method) -> nodes.Method:
        return node

    def visit_block_of_code(self, node: nodes.BlockOfCode) -> nodes.BlockOfCode:
        return node

    def visit_test(self, node: nodes.Test) -> nodes.Test:
        return node


def add_methods_to_fixtures(root: nodes.RootNode) -> nodes.RootNode:
    return root.accept(_AddMethodsToFixtures())
