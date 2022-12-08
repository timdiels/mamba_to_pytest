import typing as t

from mamba_to_pytest.node_visitors.flatten_singleton_test_contexts import flatten_singleton_test_contexts
from mamba_to_pytest.nodes import RootNode, TestContext, BlockOfCode, TestTeardown, TestSetup, Fixture, NodeBase, Test


def test_flatten_singleton_test_contexts():
    block = BlockOfCode(indent=12, body=" " * 12 + "code\n")
    root = RootNode(
        children=(
            TestContext(
                name='TestRoot',
                indent=2,
                has_as_self=False,
                children=(
                    TestContext(
                        name='TestNameThing',
                        indent=4,
                        has_as_self=False,
                        children=(
                            TestContext(
                                name='TestDeeperThing',
                                indent=7,
                                has_as_self=False,
                                children=(
                                    Test(body=block, name='test_foo_is_who', indent=9),
                                )
                            ),
                        )
                    ),
                )
            ),
        ),
    )

    root = flatten_singleton_test_contexts(root)

    assert root.children == (
        TestContext(
            indent=2,
            name='TestRoot',
            has_as_self=False,
            children=(
                Test(
                    body=BlockOfCode(indent=7, body=" " * 7 + "code\n"),
                    indent=4,
                    name='test_name_thing_deeper_thing_foo_is_who',
                ),
            ),
        ),
    )
