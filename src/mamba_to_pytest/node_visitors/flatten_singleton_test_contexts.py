from __future__ import annotations
import dataclasses

from mamba_to_pytest import nodes
from mamba_to_pytest.names import prepend_pytest_class_name_to_test_method
from mamba_to_pytest.node_visitors.base import NodeVisitor


class _FlattenSingletonTestContextsVisitor(NodeVisitor):

    def __init__(self):
        self._is_root_context = True

    def visit_root(self, node: nodes.RootNode) -> nodes.RootNode:
        return self._replace_children(node)

    def visit_test_context(self, node: nodes.TestContext) -> nodes.TestContext | nodes.Test:
        if self._is_root_context:
            # Our tests assume to be in a class, if we flatten a context at a root, we would end up with a test
            # function that still has a self, ... causes all kinds of trouble.
            self._is_root_context = False
            node = self._replace_children(node)
            self._is_root_context = True
        else:
            node = self._replace_children(node)
            if len(node.children) == 1:
                child = node.children[0]
                if isinstance(child, nodes.Test):
                    # Merge name and dedent the code
                    merged_name = prepend_pytest_class_name_to_test_method(cls_name=node.name, method_name=child.name)
                    body = child.body
                    return dataclasses.replace(
                        child,
                        name=merged_name,
                        indent=node.indent,
                        body=body.replace_indent(child.indent),
                    )
        return node

    def visit_block_of_code(self, node: nodes.BlockOfCode) -> nodes.BlockOfCode:
        return node

    def visit_test(self, node: nodes.Test) -> nodes.Test:
        return node

    def visit_test_setup(self, node: nodes.TestSetup) -> nodes.TestSetup:
        return node

    def visit_test_teardown(self, node: nodes.TestTeardown) -> nodes.TestTeardown:
        return node

    def visit_fixture(self, node: nodes.Fixture) -> nodes.Fixture:
        raise AssertionError("These don't exist yet")

    def visit_method(self, node: nodes.Method) -> nodes.Method:
        return node


def flatten_singleton_test_contexts(root: nodes.RootNode) -> nodes.RootNode:
    return root.accept(_FlattenSingletonTestContextsVisitor())
