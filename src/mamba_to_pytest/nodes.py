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
class CompositeNodeBase(NodeBase, abc.ABC):
    children: tuple[NodeBase, ...]


@dataclasses.dataclass(frozen=True)
class CodeWrapperNodeBase(NodeBase, abc.ABC):
    indent: int
    body: BlockOfCode

    def __post_init__(self):
        super().__post_init__()
        assert self.body.indent > self.indent


@dataclasses.dataclass(frozen=True)
class RootNode(CompositeNodeBase):
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


@dataclasses.dataclass(frozen=True)
class TestContext(CompositeNodeBase):
    name: str
    has_as_self: bool
    indent: int

    def __post_init__(self):
        super().__post_init__()
        assert self.children  # must have at least 1
        for child in self.children:
            assert child.indent > self.indent

    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        return visitor.visit_test_context(self)

    def __str__(self):
        return f'TestContext({self.name})'


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

    def __post_init__(self):
        assert self.setup or self.teardown
        if self.setup and self.teardown:
            assert self.setup.indent == self.teardown.indent
            assert self.setup.scope == self.teardown.scope

    def accept(self, visitor: v.NodeVisitor) -> t.Any:
        return visitor.visit_fixture(self)

    @property
    def scope(self) -> TestScope:
        return self.either.scope

    @property
    def indent(self) -> int:
        return self.either.indent

    @property
    def either(self) -> TestSetup | TestTeardown:
        either = self.setup or self.teardown
        assert either  # keep mypy happy
        return either
