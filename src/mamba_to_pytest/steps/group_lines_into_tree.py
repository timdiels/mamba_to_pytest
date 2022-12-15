from __future__ import annotations

import typing as t

from more_itertools import one, peekable

from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.lines import WithLine, MethodHeading, LineOfCode
from mamba_to_pytest.names import convert_mamba_name_to_method_name, convert_mamba_name_to_class_name
from mamba_to_pytest.nodes import NodeBase, BlockOfCode, RootNode, Test, TestTeardown, TestSetup, TestContext, Method


def group_lines_into_tree(blocks_and_lines: t.Iterable[BlockOfCode | WithLine | MethodHeading]) -> RootNode:
    children = _convert_descendants(peekable(blocks_and_lines))
    return RootNode(children=tuple(children))


def _convert_descendants(descendants: peekable[BlockOfCode | WithLine | MethodHeading]) -> t.Iterable[NodeBase]:
    """Convert child nodes of a parent WithLine or the root"""
    for descendant in descendants:
        if isinstance(descendant, WithLine) or isinstance(descendant, MethodHeading):
            heading = descendant
            heading_descendants = peekable(_iter_descendants_of_parent(descendants, parent_indent=heading.indent))
            children = tuple(_convert_descendants(heading_descendants))
            yield _convert_block_heading(heading, children)
        else:
            yield descendant


def _iter_descendants_of_parent(
        blocks_and_lines: peekable[BlockOfCode | WithLine | MethodHeading], parent_indent: int
) -> t.Iterable[BlockOfCode | WithLine | MethodHeading]:
    while blocks_and_lines and blocks_and_lines.peek().indent > parent_indent:
        yield next(blocks_and_lines)


def _convert_block_heading(line: WithLine | MethodHeading, children: tuple[NodeBase, ...]) -> NodeBase:
    if isinstance(line, WithLine):
        return _convert_with_line(line, children)
    else:
        return Method(
            indent=line.indent,
            name=line.name,
            body=_get_single_block_child(line, children),
            tail=line.line[line.indent:],
        )


def _convert_with_line(line: WithLine, children: tuple[NodeBase, ...]) -> NodeBase:
    assert not line.comment
    if line.variable in ('description', 'context', 'describe'):
        assert line.name, f'Encountered nameless {line.variable}():\n{line.line}'
        return TestContext(
            indent=line.indent,
            name=convert_mamba_name_to_class_name(line.name),
            other_children=children,
            class_fixture=None,
            method_fixture=None,
        )
    elif line.variable in ('before.each', 'before.all', 'after.each', 'after.all'):
        assert not line.name

        cls: t.Type[TestSetup] | t.Type[TestTeardown]
        if line.variable.startswith('before'):
            cls = TestSetup
        else:
            cls = TestTeardown

        if line.variable.endswith('each'):
            scope = TestScope.METHOD
        else:
            scope = TestScope.CLASS

        return cls(
            scope=scope,
            body=_get_single_block_child(line, children),
            indent=line.indent,
        )
    else:
        assert line.variable == 'it'
        assert line.name, f'Encountered nameless it():\n{line.line}'
        return Test(
            indent=line.indent,
            name=convert_mamba_name_to_method_name(line.name),
            body=_get_single_block_child(line, children),
        )


def _get_single_block_child(line: LineOfCode, children: tuple[NodeBase, ...]) -> BlockOfCode:
    try:
        child = one(children)
    except ValueError as exc:
        children_str = '\n'.join(str(child) for child in children)
        raise Exception(f'line:\n{line.line}\nhas multiple/no children:\n{children_str}') from exc

    if not isinstance(child, BlockOfCode):
        raise Exception(f'line:\n{line.line}\nshould have a code block as child, but instead got {child}')

    return child
