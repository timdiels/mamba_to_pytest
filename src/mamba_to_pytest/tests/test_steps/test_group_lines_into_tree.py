from __future__ import annotations
import typing as t
from functools import partial

import pytest
from more_itertools import one

from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.lines import WithLine, MethodHeading
from mamba_to_pytest.nodes import Test, BlockOfCode, TestSetup, TestTeardown, TestContext, Method, NodeBase
from mamba_to_pytest.steps.group_lines_into_tree import group_lines_into_tree

create_context = partial(TestContext, class_fixture=None, method_fixture=None)


class TestConvertWithLines:
    @pytest.mark.parametrize(
        'variable,cls,scope',
        (
            ('before.each', TestSetup, TestScope.METHOD),
            ('before.all', TestSetup, TestScope.CLASS),
            ('after.each', TestTeardown, TestScope.METHOD),
            ('after.all', TestTeardown, TestScope.CLASS),
        ),
    )
    def test_setup_teardown_node(self, variable, cls: t.Type[TestSetup | TestTeardown], scope: TestScope):
        block = BlockOfCode(indent=3, body='   body1\n')
        blocks_and_lines: list[BlockOfCode | WithLine] = [
            WithLine(indent=2, line='with var1:\n', variable=variable, name=None, comment=None),
            block,
        ]

        root = group_lines_into_tree(blocks_and_lines)

        # noinspection PyArgumentList
        assert root.children == (cls(body=block, scope=scope, indent=2),)

    def test_test_node(self):
        block = BlockOfCode(indent=3, body='   body1\n')
        blocks_and_lines = [
            WithLine(indent=2, line='with var1:\n', variable='it', name='name 1', comment=None),
            block,
        ]

        root = group_lines_into_tree(blocks_and_lines)

        assert root.children == (
            Test(indent=2, name='test_name_1', body=block),
        )

    def test_context_node_and_nesting(self):
        top_block = BlockOfCode(indent=2, body='   top body\n')
        child_block = BlockOfCode(indent=3, body='   child body\n')
        deep_block = BlockOfCode(indent=4, body='   deep body\n')
        blocks_and_lines = [
            top_block,
            WithLine(
                indent=2, line='with var1:\n', variable='description', name='name 1', comment=None
            ),
            child_block,
            WithLine(
                indent=3, line='with var1:\n', variable='describe', name='name 2', comment=None
            ),
            deep_block,
            deep_block,
            child_block,
            top_block,
        ]

        root = group_lines_into_tree(blocks_and_lines)

        assert root.children == (
            top_block,
            create_context(
                indent=2,
                name='TestName1',
                other_children=(
                    child_block,
                    create_context(
                        indent=3,
                        name='TestName2',
                        other_children=(deep_block, deep_block),
                    ),
                    child_block,
                ),
            ),
            top_block,
        )


def test_convert_method_heading():
    block = BlockOfCode(indent=2, body='body\n')
    blocks_and_lines = (
        MethodHeading(indent=1, line=' original line\n', name='foo'),
        block,
    )

    root = group_lines_into_tree(blocks_and_lines)

    assert one(root.children) == Method(
        indent=1,
        body=block,
        name='foo',
        tail='original line\n'
    )
