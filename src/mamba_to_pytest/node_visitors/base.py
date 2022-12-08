from __future__ import annotations
import abc
import dataclasses
import typing as t

from mamba_to_pytest import nodes


if t.TYPE_CHECKING:
    N = t.TypeVar('N', bound=nodes.NodeBase)


class NodeVisitor(abc.ABC):
    @abc.abstractmethod
    def visit_root(self, node: nodes.RootNode) -> t.Any:
        ...

    @abc.abstractmethod
    def visit_block_of_code(self, node: nodes.BlockOfCode) -> t.Any:
        ...

    @abc.abstractmethod
    def visit_test(self, node: nodes.Test) -> t.Any:
        ...

    @abc.abstractmethod
    def visit_test_context(self, node: nodes.TestContext) -> t.Any:
        ...

    @abc.abstractmethod
    def visit_test_setup(self, node: nodes.TestSetup) -> t.Any:
        ...

    @abc.abstractmethod
    def visit_test_teardown(self, node: nodes.TestTeardown) -> t.Any:
        ...

    @abc.abstractmethod
    def visit_fixture(self, node: nodes.Fixture) -> t.Any:
        ...

    def _visit_children(self, node: nodes.NodeBase) -> t.Collection[t.Any]:
        return tuple(child.accept(visitor=self) for child in self._get_children(node))

    @staticmethod
    def _get_children(node: nodes.NodeBase) -> t.Iterable[nodes.NodeBase]:
        if isinstance(node, nodes.CompositeNodeBase):
            yield from node.children
        elif isinstance(node, nodes.CodeWrapperNodeBase):
            yield node.body
        else:
            assert isinstance(node, nodes.Fixture)
            if node.setup:
                yield node.setup
            if node.teardown:
                yield node.teardown

    def _replace_children(self, node: N) -> N:
        if isinstance(node, nodes.CompositeNodeBase):
            return dataclasses.replace(  # type: ignore
                node, children=tuple(child.accept(self) for child in node.children)
            )
        elif isinstance(node, nodes.CodeWrapperNodeBase):
            return dataclasses.replace(node, body=node.body.accept(self))  # type: ignore
        else:
            assert isinstance(node, nodes.Fixture)
            return dataclasses.replace(  # type: ignore
                node,
                setup=node.setup.accept(self) if node.setup else None,
                teardown=node.teardown.accept(self) if node.teardown else None,
            )
