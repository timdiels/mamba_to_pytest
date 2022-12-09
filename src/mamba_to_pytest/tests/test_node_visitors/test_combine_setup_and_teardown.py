from __future__ import annotations
from functools import partial

from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.combine_setup_teardown import combine_setup_teardown
from mamba_to_pytest.nodes import RootNode, TestContext, BlockOfCode, TestTeardown, TestSetup, Fixture


create_context = partial(TestContext, class_fixture=None, method_fixture=None)


def create_fixture(setup_body: BlockOfCode | None, teardown_body: BlockOfCode | None, scope: TestScope) -> Fixture:
    if setup_body:
        setup = TestSetup(body=setup_body, scope=scope, indent=2)
    else:
        setup = None

    if teardown_body:
        teardown = TestTeardown(body=teardown_body, scope=scope, indent=2)
    else:
        teardown = None

    return Fixture(
        setup=setup,
        teardown=teardown,
        methods=(),
        indent=2,
        scope=scope,
    )


def test_combine_same_scope_and_move_on_top():
    block = BlockOfCode(indent=2, body="code")
    deep_block = BlockOfCode(indent=3, body="code")
    root = RootNode(
        children=(
            create_context(
                indent=1,
                name='TestName',
                has_as_self=False,
                other_children=(
                    block,
                    TestTeardown(body=deep_block, scope=TestScope.CLASS, indent=2),
                    TestTeardown(body=deep_block, scope=TestScope.METHOD, indent=2),
                    block,
                    TestSetup(body=deep_block, scope=TestScope.CLASS, indent=2),
                    TestSetup(body=deep_block, scope=TestScope.METHOD, indent=2),
                    block,
                ),
            ),
        ),
    )
    
    root = combine_setup_teardown(root)
    
    assert root.children == (
        create_context(
            indent=1,
            name='TestName',
            has_as_self=False,
            class_fixture=create_fixture(setup_body=deep_block, teardown_body=deep_block, scope=TestScope.CLASS),
            method_fixture=create_fixture(setup_body=deep_block, teardown_body=deep_block, scope=TestScope.METHOD),
            other_children=(
                # Order of class/method fixture does not matter but we might as well give it a consistent order
                block,
                block,
                block,
            ),
        ),
    )


def test_setup_or_teardown_can_be_missing():
    block = BlockOfCode(indent=3, body="code")
    root = RootNode(
        children=(
            create_context(
                indent=1,
                name='TestName',
                has_as_self=False,
                other_children=(
                    TestSetup(body=block, scope=TestScope.METHOD, indent=2),
                    TestTeardown(body=block, scope=TestScope.CLASS, indent=2),
                ),
            ),
        ),
    )

    root = combine_setup_teardown(root)

    assert root.children == (
        create_context(
            indent=1,
            name='TestName',
            has_as_self=False,
            class_fixture=create_fixture(
                setup_body=None,
                teardown_body=block,
                scope=TestScope.CLASS,
            ),
            method_fixture=create_fixture(
                setup_body=block,
                teardown_body=None,
                scope=TestScope.METHOD,
            ),
            other_children=(),
        ),
    )


def test_both_can_be_missing():
    block = BlockOfCode(indent=2, body="code")
    root = RootNode(
        children=(
            create_context(
                indent=1,
                name='TestName',
                has_as_self=False,
                other_children=(
                    block,
                ),
            ),
        ),
    )

    new_root = combine_setup_teardown(root)

    assert new_root == root
