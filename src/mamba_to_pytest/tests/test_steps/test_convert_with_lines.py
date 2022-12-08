from __future__ import annotations
import typing as t

import pytest
from more_itertools import one

from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.lines import WithLine, LineOfCode
from mamba_to_pytest.nodes import Test, BlockOfCode, TestSetup, TestTeardown, TestContext
from mamba_to_pytest.steps.convert_with_lines import convert_with_lines, \
    split_off_comments


def test_split_off_comments():
    line = LineOfCode(indent=0, line='leave me alone\n'),
    lines = [
        WithLine(
            indent=2, line='with var1:\n', variable='it', name='name 1', comment='# comment 1', has_as_self=False
        ),
        line,
    ]

    lines = tuple(split_off_comments(lines))

    assert lines == (
        LineOfCode(indent=2, line="  # comment 1\n"),
        WithLine(indent=2, line='with var1:\n', variable='it', name='name 1', comment=None, has_as_self=False),
        line,
    )


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
            WithLine(indent=2, line='with var1:\n', variable=variable, name=None, comment=None, has_as_self=False),
            block,
        ]

        root = convert_with_lines(blocks_and_lines)

        # noinspection PyArgumentList
        assert root.children == (cls(body=block, scope=scope, indent=2),)

    def test_test_node(self):
        block = BlockOfCode(indent=3, body='   body1\n')
        blocks_and_lines = [
            WithLine(indent=2, line='with var1:\n', variable='it', name='name 1', comment=None, has_as_self=False),
            block,
        ]

        root = convert_with_lines(blocks_and_lines)

        assert root.children == (
            Test(indent=2, name='test_name_1', body=block),
        )

    def test_context_node(self):
        top_block = BlockOfCode(indent=2, body='   top body\n')
        child_block = BlockOfCode(indent=3, body='   child body\n')
        deep_block = BlockOfCode(indent=4, body='   deep body\n')
        blocks_and_lines = [
            top_block,
            WithLine(
                indent=2, line='with var1:\n', variable='description', name='name 1', comment=None, has_as_self=True
            ),
            child_block,
            WithLine(
                indent=3, line='with var1:\n', variable='describe', name='name 2', comment=None, has_as_self=False
            ),
            deep_block,
            deep_block,
            child_block,
            top_block,
        ]

        root = convert_with_lines(blocks_and_lines)

        assert root.children == (
            top_block,
            TestContext(
                indent=2,
                name='TestName1',
                has_as_self=True,
                children=(
                    child_block,
                    TestContext(indent=3, name='TestName2', has_as_self=False, children=(deep_block, deep_block)),
                    child_block,
                ),
            ),
            top_block,
        )
