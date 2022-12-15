"""
Poor man's AST

ast.parse/unparse does not preserve comments, formatting, ... unparse also doesn't work for complex cases,
though nor does my AST.
"""

from __future__ import annotations

import abc
import dataclasses
import typing as t

from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors import base as v


@dataclasses.dataclass(frozen=True)
class NodeBase(abc.ABC):
    def __post_init__(self):
        assert self.indent >= 0

    @abc.abstractmethod
    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        ...


@dataclasses.dataclass(frozen=True)
class CodeWrapperNodeBase(NodeBase, abc.ABC):
    indent: int
    body: BlockOfCode

    def __post_init__(self):
        super().__post_init__()
        assert self.body.indent > self.indent


@dataclasses.dataclass(frozen=True)
class RootNode(NodeBase):
    children: tuple[NodeBase, ...]

    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        return visitor.visit_root(self)

    @property
    def indent(self) -> int:
        return 0


@dataclasses.dataclass(frozen=True)
class BlockOfCode(NodeBase):
    indent: int
    body: str

    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        return visitor.visit_block_of_code(self)

    def replace_indent(self, indent: int) -> BlockOfCode:
        return dataclasses.replace(
            self,
            indent=indent,
            body='\n'.join(self._reindent_lines(indent)) + '\n',
        )

    def _reindent_lines(self, indent: int) -> t.Iterable[str]:
        for line in self.body.splitlines():
            # Comments can have less indent than the block, because we treated those lines as having no indent. We
            # need to be careful not to chop off the actual front of a comment when dedenting beyond its indent.
            line_indent = len(line) - len(line.lstrip())
            if line_indent == 0 and line.startswith('#'):
                # These should probably be left alone, they tend to be whole blocks of commented code.
                yield line
            else:
                yield ' ' * indent + line[min(self.indent, line_indent):]


@dataclasses.dataclass(frozen=True)
class TestContext(NodeBase):
    name: str
    indent: int
    class_fixture: Fixture | None
    method_fixture: Fixture | None
    other_children: tuple[NodeBase, ...]

    def __post_init__(self):
        super().__post_init__()
        assert self.children  # must have at least 1
        if self.class_fixture:
            assert self.class_fixture.scope == TestScope.CLASS
        if self.method_fixture:
            assert self.method_fixture.scope == TestScope.METHOD
        for child in self.children:
            assert child.indent > self.indent
        for child in self.other_children:
            assert not isinstance(child, Fixture)

    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        return visitor.visit_test_context(self)

    def __str__(self):
        return f'TestContext({self.name})'

    @property
    def children(self) -> tuple[NodeBase, ...]:
        return tuple(self._iter_children())

    def _iter_children(self) -> t.Iterable[NodeBase]:
        if self.class_fixture:
            yield self.class_fixture
        if self.method_fixture:
            yield self.method_fixture
        yield from self.other_children


@dataclasses.dataclass(frozen=True)
class Test(CodeWrapperNodeBase):
    name: str

    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        return visitor.visit_test(self)

    def __str__(self):
        return f'Test({self.name})'


@dataclasses.dataclass(frozen=True)
class TestSetup(CodeWrapperNodeBase):
    scope: TestScope

    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        return visitor.visit_test_setup(self)


@dataclasses.dataclass(frozen=True)
class TestTeardown(CodeWrapperNodeBase):
    scope: TestScope

    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        return visitor.visit_test_teardown(self)


@dataclasses.dataclass(frozen=True)
class Fixture(NodeBase):
    setup: TestSetup | None
    teardown: TestTeardown | None
    methods: tuple[Method, ...]
    scope: TestScope
    indent: int

    def __post_init__(self):
        assert self.setup or self.teardown or self.methods
        assert self.indent < self.body_indent

        if self.scope == TestScope.CLASS:
            assert not self.methods

        if self.setup:
            assert self.setup.indent == self.indent
            assert self.setup.scope == self.scope
            assert self.setup.body.indent == self.body_indent

        if self.teardown:
            assert self.teardown.indent == self.indent
            assert self.teardown.scope == self.scope
            assert self.teardown.body.indent == self.body_indent

        for method in self.methods:
            assert method.indent == self.body_indent

    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        return visitor.visit_fixture(self)

    @property
    def body_indent(self):
        either = self.setup or self.teardown
        if either:
            return either.body.indent
        return self.methods[0].indent


@dataclasses.dataclass(frozen=True)
class Method(CodeWrapperNodeBase):
    """
    The node analog to a MethodHeading line

    Looks like a method, i.e. has a self param, but never actually appears inside a class because we weeded those out
    in one of the steps.
    """

    name: str
    tail: str

    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        return visitor.visit_method(self)

    def __str__(self):
        return f'Method({self.name})'

    def replace_indent(self, indent: int) -> Method:
        return dataclasses.replace(
            self,
            indent=indent,
            body=self.body.replace_indent(indent + 4),
        )
