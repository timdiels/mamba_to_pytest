from __future__ import annotations
import typing as t

from mamba_to_pytest import nodes
from mamba_to_pytest.node_visitors.base import NodeVisitor


class _WriteVisitor(NodeVisitor):

    def visit_root(self, node: nodes.RootNode) -> None:
        self._visit_children(node)

    def visit_block_of_code(self, node: nodes.BlockOfCode) -> None:
        self._out.write(node.body)

    def visit_test(self, node: nodes.Test) -> None:
        raise AssertionError("Should no longer exist")

    def visit_test_context(self, node: nodes.TestContext) -> None:
        self._out.write(' ' * node.indent + f'class {node.name}:\n')
        self._visit_children(node)

    def visit_test_setup(self, node: nodes.TestSetup) -> None:
        raise AssertionError("Should no longer exist")

    def visit_test_teardown(self, node: nodes.TestTeardown) -> None:
        raise AssertionError("Should no longer exist")

    def visit_fixture(self, node: nodes.Fixture) -> None:
        raise AssertionError("Should no longer exist")

    def __init__(self, out: t.TextIO):
        self._out = out


def write_tree(root: nodes.RootNode, out: t.TextIO) -> None:
    root.accept(_WriteVisitor(out))
