from __future__ import annotations
import dataclasses
import typing

from mamba_to_pytest import nodes
from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.base import NodeVisitor


class _CombineSetupAndTeardownVisitor(NodeVisitor):

    def visit_root(self, node: nodes.RootNode) -> nodes.RootNode:
        return self._replace_children(node)

    def visit_block_of_code(self, node: nodes.BlockOfCode) -> nodes.BlockOfCode:
        return node

    def visit_test(self, node: nodes.Test) -> nodes.Test:
        return node

    def visit_test_setup(self, node: nodes.TestSetup) -> nodes.TestSetup:
        raise AssertionError("Parent should combine these instead of visiting them")

    def visit_test_teardown(self, node: nodes.TestTeardown) -> nodes.TestTeardown:
        raise AssertionError("Parent should combine these instead of visiting them")

    def visit_fixture(self, node: nodes.Fixture) -> nodes.Fixture:
        raise AssertionError("These don't exist yet")

    def visit_test_context(self, node: nodes.TestContext) -> nodes.TestContext:
        setup_nodes, teardown_nodes, other_children = self._split_children(node)
        other_children = (child.accept(self) for child in other_children)
        fixtures = self._combine_setup_and_teardown(setup_nodes, teardown_nodes)
        return dataclasses.replace(node, children=(*fixtures, *other_children))

    @staticmethod
    def _split_children(node):
        setup_nodes: dict[TestScope, nodes.TestSetup] = {}
        teardown_nodes: dict[TestScope, nodes.TestTeardown] = {}
        other_children = []
        for child in node.children:
            if isinstance(child, nodes.TestSetup):
                assert child.scope not in setup_nodes  # multiple setups of same scope not supported
                setup_nodes[child.scope] = child
            elif isinstance(child, nodes.TestTeardown):
                assert child.scope not in teardown_nodes  # multiple teardowns of same scope not supported
                teardown_nodes[child.scope] = child
            else:
                other_children.append(child)
        return setup_nodes, teardown_nodes, other_children

    @staticmethod
    def _combine_setup_and_teardown(
            setup_nodes: dict[TestScope, nodes.TestSetup], teardown_nodes: dict[TestScope, nodes.TestTeardown]
    ) -> typing.Iterable[nodes.Fixture]:
        for scope in (TestScope.CLASS, TestScope.METHOD):
            if scope in setup_nodes or scope in teardown_nodes:
                yield nodes.Fixture(
                    setup=setup_nodes.get(scope),
                    teardown=teardown_nodes.get(scope)
                )


def combine_setup_teardown(root: nodes.RootNode) -> nodes.RootNode:
    return root.accept(_CombineSetupAndTeardownVisitor())
