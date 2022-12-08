from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.combine_setup_teardown import combine_setup_teardown
from mamba_to_pytest.nodes import RootNode, TestContext, BlockOfCode, TestTeardown, TestSetup, Fixture


def test_combine_same_scope_and_move_on_top():
    block = BlockOfCode(indent=2, body="code")
    deep_block = BlockOfCode(indent=3, body="code")
    root = RootNode(
        children=(
            TestContext(
                indent=1,
                name='TestName',
                has_as_self=False,
                children=(
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
        TestContext(
            indent=1,
            name='TestName',
            has_as_self=False,
            children=(
                # Order of class/method fixture does not matter but we might as well give it a consistent order
                Fixture(
                    setup=TestSetup(body=deep_block, scope=TestScope.CLASS, indent=2),
                    teardown=TestTeardown(body=deep_block, scope=TestScope.CLASS, indent=2),
                ),
                Fixture(
                    setup=TestSetup(body=deep_block, scope=TestScope.METHOD, indent=2),
                    teardown=TestTeardown(body=deep_block, scope=TestScope.METHOD, indent=2),
                ),
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
            TestContext(
                indent=1,
                name='TestName',
                has_as_self=False,
                children=(
                    TestSetup(body=block, scope=TestScope.METHOD, indent=2),
                    TestTeardown(body=block, scope=TestScope.CLASS, indent=2),
                ),
            ),
        ),
    )

    root = combine_setup_teardown(root)

    assert root.children == (
        TestContext(
            indent=1,
            name='TestName',
            has_as_self=False,
            children=(
                Fixture(
                    setup=None,
                    teardown=TestTeardown(body=block, scope=TestScope.CLASS, indent=2),
                ),
                Fixture(
                    setup=TestSetup(body=block, scope=TestScope.METHOD, indent=2),
                    teardown=None,
                ),
            ),
        ),
    )


def test_both_can_be_missing():
    block = BlockOfCode(indent=2, body="code")
    root = RootNode(
        children=(
            TestContext(
                indent=1,
                name='TestName',
                has_as_self=False,
                children=(
                    block,
                ),
            ),
        ),
    )

    new_root = combine_setup_teardown(root)

    assert new_root == root
