from __future__ import annotations
import dataclasses
import io
import re

from mamba_to_pytest import nodes
from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.base import NodeVisitor


_SELF_PATTERN = re.compile(r'(^|\W)self(\W|$)')


class _ConvertSelfVars(NodeVisitor):
    def __init__(self):
        self._current_fixture: nodes.Fixture | None = None
        self._uses_pytest_pkg = False
        self._other_count: int = 0
        self._in_self_scope = False
        self._replaced_self_vars: bool = False

    def visit_root(self, node: nodes.RootNode) -> nodes.RootNode:
        node = self._replace_children(node)
        if self._uses_pytest_pkg:
            children = (
                nodes.BlockOfCode(indent=0, body='import pytest\n'),
                *node.children,
            )
            node = dataclasses.replace(node, children=children)
        return node

    def visit_test_context(self, node: nodes.TestContext) -> nodes.TestContext:
        starts_self_scope = node.has_as_self and not self._in_self_scope
        if node.has_as_self and self._in_self_scope:
            print(f"Warning: Ignoring nested `as self` of {node}")
        if starts_self_scope:
            self._in_self_scope = True

        node = self._replace_children(node)

        if starts_self_scope:
            self._in_self_scope = False
        return node

    def visit_test(self, node: nodes.Test) -> nodes.BlockOfCode:
        self._replaced_self_vars = False
        node = self._replace_children(node)

        params = ['self']
        fixture_name = TestScope.METHOD.fixture_name
        if self._replaced_self_vars:
            params.append(fixture_name)
        params_str = ", ".join(params)

        indent_str = ' ' * node.indent
        return nodes.BlockOfCode(
            indent=node.indent,
            body=f"{indent_str}def {node.name}({params_str}):\n{node.body.body}",
        )

    def visit_method(self, node: nodes.Method) -> nodes.Method:
        return self._replace_children(node)

    def visit_test_setup(self, node: nodes.TestSetup) -> nodes.TestSetup:
        return self._replace_children(node)

    def visit_test_teardown(self, node: nodes.TestTeardown) -> nodes.TestTeardown:
        return self._replace_children(node)

    def visit_fixture(self, node: nodes.Fixture) -> nodes.BlockOfCode:
        self._uses_pytest_pkg = True
        self._current_fixture = node
        self._replaced_self_vars = False
        node = self._replace_children(node)
        self._current_fixture = None

        if node.scope == TestScope.CLASS:
            pytest_scope = ', scope="class"'
        else:
            pytest_scope = ''

        code = io.StringIO()
        indent_str = ' ' * node.indent
        body_indent_str = ' ' * node.body_indent
        fixture_has_return = self._replaced_self_vars or node.methods
        if fixture_has_return:
            fixture_name = node.scope.fixture_name
        else:
            self._other_count += 1
            fixture_name = f'mamba_other{self._other_count}'

        code.write(f'{indent_str}@pytest.fixture(autouse=True{pytest_scope})\n')
        if fixture_has_return:
            code.write(f'{indent_str}def {fixture_name}(self, {fixture_name}):\n')
        else:
            code.write(f'{indent_str}def {fixture_name}(self):\n')

        for method in node.methods:
            code.write(' ' * method.indent + method.tail)
            code.write(method.body.body)

        if fixture_has_return:
            code.write(f'{body_indent_str}{fixture_name} = {fixture_name}.copy()\n')

        for method in node.methods:
            # Write method assignments
            code.write(f'{body_indent_str}mamba.{method.name} = {method.name}\n')

        if node.setup:
            code.write(node.setup.body.body.rstrip('\n') + '\n')

        if fixture_has_return:
            code.write(f'{body_indent_str}yield {fixture_name}\n')
        elif node.teardown:
            code.write(f'{body_indent_str}yield\n')

        if node.teardown:
            code.write(node.teardown.body.body)
        else:
            code.write('\n')

        return nodes.BlockOfCode(body=code.getvalue(), indent=node.indent)

    def visit_block_of_code(self, node: nodes.BlockOfCode) -> nodes.BlockOfCode:
        if self._in_self_scope:
            if self._current_fixture:
                fixture_name = self._current_fixture.scope.fixture_name
            else:
                fixture_name = TestScope.METHOD.fixture_name
            body = _SELF_PATTERN.sub(rf'\1{fixture_name}\2', node.body)
            if body != node.body:
                self._replaced_self_vars = True
            node = dataclasses.replace(node, body=body)
        return node


def convert_self_vars(root: nodes.RootNode) -> nodes.RootNode:
    return root.accept(_ConvertSelfVars())
