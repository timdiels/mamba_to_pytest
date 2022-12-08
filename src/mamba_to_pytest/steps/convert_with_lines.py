from __future__ import annotations

import dataclasses
import typing as t

from more_itertools import one, peekable

from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.lines import LineOfCode, WithLine, BlankLine
from mamba_to_pytest.names import convert_mamba_name_to_method_name, convert_mamba_name_to_class_name
from mamba_to_pytest.nodes import NodeBase, BlockOfCode, RootNode, Test, TestTeardown, TestSetup, TestContext


def split_off_comments(lines: t.Iterable[LineOfCode | BlankLine]) -> t.Iterable[LineOfCode | BlankLine]:
    for line in lines:
        if isinstance(line, WithLine) and line.comment:
            yield LineOfCode(indent=line.indent, line=' ' * line.indent + line.comment + '\n')
            yield dataclasses.replace(line, comment=None)
        else:
            yield line


def convert_with_lines(blocks_and_lines: t.Iterable[BlockOfCode | WithLine]) -> RootNode:
    children = _convert_descendants(peekable(blocks_and_lines))
    return RootNode(children=tuple(children))


def _convert_descendants(descendants: peekable[BlockOfCode | WithLine]) -> t.Iterable[NodeBase]:
    """Convert child nodes of a parent WithLine or the root"""
    for descendant in descendants:
        if isinstance(descendant, WithLine):
            line = descendant
            with_line_descendants = peekable(_iter_descendants_of_parent(descendants, parent_indent=line.indent))
            children = tuple(_convert_descendants(with_line_descendants))
            yield from _convert_with_line(line, children)
        else:
            yield descendant


def _iter_descendants_of_parent(
        blocks_and_lines: peekable[BlockOfCode | WithLine], parent_indent: int
) -> t.Iterable[BlockOfCode | WithLine]:
    while blocks_and_lines and blocks_and_lines.peek().indent > parent_indent:
        yield next(blocks_and_lines)


def _convert_with_line(line: WithLine, children: tuple[NodeBase, ...]) -> t.Iterable[NodeBase]:
    assert not line.comment
    if line.variable in ('description', 'context', 'describe'):
        assert line.name, f'Encountered nameless {line.variable}():\n{line.line}'
        yield TestContext(
            indent=line.indent,
            name=convert_mamba_name_to_class_name(line.name),
            children=children,
            has_as_self=line.has_as_self,
        )
    elif line.variable in ('before.each', 'before.all', 'after.each', 'after.all'):
        assert not line.name
        assert not line.has_as_self

        cls: t.Type[TestSetup] | t.Type[TestTeardown]
        if line.variable.startswith('before'):
            cls = TestSetup
        else:
            cls = TestTeardown

        if line.variable.endswith('each'):
            scope = TestScope.METHOD
        else:
            scope = TestScope.CLASS

        yield cls(
            scope=scope,
            body=_get_single_block_child(line, children),
            indent=line.indent,
        )
    else:
        assert line.variable == 'it'
        assert line.name, f'Encountered nameless it():\n{line.line}'
        assert not line.has_as_self
        yield Test(
            indent=line.indent,
            name=convert_mamba_name_to_method_name(line.name),
            body=_get_single_block_child(line, children),
        )


def _get_single_block_child(line: WithLine, children: tuple[NodeBase, ...]) -> BlockOfCode:
    try:
        child = one(children)
    except ValueError as exc:
        children_str = '\n'.join(str(child) for child in children)
        raise Exception(f'it("{line.name}") has multiple/no children:\n{children_str}') from exc

    if not isinstance(child, BlockOfCode):
        raise Exception(f'it("{line.name}") should have a code block as child, but instead got {child}')

    return child
