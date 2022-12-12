from __future__ import annotations
import dataclasses
import io
import re

from mamba_to_pytest import nodes
from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.base import NodeVisitor


_SELF_VAR_ASSIGNMENT_PATTERN = re.compile(r'(self[.][a-zA-Z0-9_]+)\s*=[^=]')
_SELF_PATTERN = re.compile(r'(\W)self([^.\w])')  # in some cases replace self despite not having seen it in self vars


_SelfVars = frozenset[str]
_VarScopes = dict[nodes.TestContext, _SelfVars]


class _CollectSelfVars(NodeVisitor):
    def __init__(self):
        self._var_scopes: _VarScopes = {}
        self._in_scope = False

    def visit_root(self, node: nodes.RootNode) -> _VarScopes:
        self._visit_children(node)
        return self._var_scopes

    def visit_test_context(self, node: nodes.TestContext) -> _SelfVars:
        starts_self_vars_scope = False
        if node.has_as_self:
            if self._in_scope:
                print(f"Warning: Ignoring nested `as self` of {node}")
            else:
                starts_self_vars_scope = True
                self._in_scope = True

        # Always visit children so descendants are validated too
        child_vars = frozenset.union(*(child.accept(self) for child in node.children))

        if starts_self_vars_scope:
            if child_vars:
                self._var_scopes[node] = child_vars
            self._in_scope = False

        if self._in_scope:
            return child_vars
        else:
            return frozenset()

    def visit_fixture(self, node: nodes.Fixture) -> _SelfVars:
        all_self_vars: list[_SelfVars] = []
        if node.setup:
            all_self_vars.append(node.setup.accept(self))
        if node.teardown:
            all_self_vars.append(node.teardown.accept(self))
        all_self_vars.extend(method.accept(self) for method in node.methods)
        return frozenset.union(*all_self_vars)

    def visit_test_setup(self, node: nodes.TestSetup) -> _SelfVars:
        return node.body.accept(self)

    def visit_test_teardown(self, node: nodes.TestTeardown) -> _SelfVars:
        return node.body.accept(self)

    def visit_test(self, node: nodes.Test) -> _SelfVars:
        return node.body.accept(self)

    def visit_method(self, node: nodes.Method) -> _SelfVars:
        return node.body.accept(self) | frozenset({f'self.{node.name}'})

    def visit_block_of_code(self, node: nodes.BlockOfCode) -> _SelfVars:
        return frozenset(
            match.group(1) for match in _SELF_VAR_ASSIGNMENT_PATTERN.finditer(node.body)
        )


class _ConvertSelfVars(NodeVisitor):
    def __init__(self, var_scopes: _VarScopes):
        self._var_scopes = var_scopes
        self._current_vars: _SelfVars | None = None
        self._current_fixture: nodes.Fixture | None = None
        self._uses_pytest_pkg = False
        self._other_count: int = 0

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
        if node in self._var_scopes:
            assert not self._current_vars  # Recursive `as self` not supported
            self._current_vars = self._var_scopes[node]
            node = self._replace_children(node)
            self._current_vars = None
            return node
        else:
            return self._replace_children(node)

    def visit_test(self, node: nodes.Test) -> nodes.BlockOfCode:
        node = self._replace_children(node)

        params = ['self']
        fixture_name = TestScope.METHOD.fixture_name
        if self._current_vars and f'{fixture_name}.' in node.body.body:
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
        node = self._replace_children(node)
        self._current_fixture = None

        if node.scope == TestScope.CLASS:
            pytest_scope = ', scope="class"'
        else:
            pytest_scope = ''

        code = io.StringIO()
        indent_str = ' ' * node.indent
        body_indent_str = ' ' * node.body_indent
        fixture_has_return = self._current_vars or node.methods
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
        if self._current_vars:
            if self._current_fixture:
                fixture_name = self._current_fixture.scope.fixture_name
            else:
                fixture_name = TestScope.METHOD.fixture_name
            body = node.body
            for var in self._current_vars:
                body = body.replace(var, f"{fixture_name}{var[len('self'):]}")
            body = _SELF_PATTERN.sub(rf'\1{fixture_name}\2', body)
            return dataclasses.replace(node, body=body)
        else:
            return node


def convert_self_vars(root: nodes.RootNode) -> nodes.RootNode:
    var_scopes = root.accept(_CollectSelfVars())
    return root.accept(_ConvertSelfVars(var_scopes))
