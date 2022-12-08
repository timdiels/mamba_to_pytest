from __future__ import annotations

import typing as t

from mamba_to_pytest import nodes
from mamba_to_pytest.node_visitors.base import NodeVisitor


class _ValidationVisitor(NodeVisitor):

    def visit_root(self, node: nodes.RootNode) -> None:
        self._assert_no_duplicate_names(node.children)
        self._visit_children(node)

    def visit_test_context(self, node: nodes.TestContext) -> None:
        self._assert_no_duplicate_names(node.children)
        self._visit_children(node)

    def visit_test_setup(self, node: nodes.TestSetup) -> None:
        self._visit_children(node)

    def visit_test_teardown(self, node: nodes.TestTeardown) -> None:
        self._visit_children(node)

    def visit_fixture(self, node: nodes.Fixture) -> None:
        self._visit_children(node)

    def visit_block_of_code(self, node: nodes.BlockOfCode) -> None:
        pass

    def visit_test(self, node: nodes.Test) -> None:
        pass

    @staticmethod
    def _assert_no_duplicate_names(children: t.Iterable[nodes.NodeBase]):
        seen = set()
        for child in children:
            if isinstance(child, nodes.Test) or isinstance(child, nodes.TestContext):
                if child.name in seen:
                    raise AssertionError(
                        f'Ended up with duplicate pytest name, please rename it in the mamba file: {child.name}'
                    )
                seen.add(child.name)


def validate_node(root: nodes.RootNode):
    root.accept(_ValidationVisitor())
