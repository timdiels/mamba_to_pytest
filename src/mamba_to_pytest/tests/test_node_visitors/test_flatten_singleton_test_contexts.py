from functools import partial

from mamba_to_pytest.node_visitors.flatten_singleton_test_contexts import flatten_singleton_test_contexts
from mamba_to_pytest.nodes import RootNode, TestContext, BlockOfCode, Test


create_context = partial(TestContext, class_fixture=None, method_fixture=None)


def test_flatten_singleton_test_contexts():
    block = BlockOfCode(indent=12, body=" " * 12 + "code\n")
    root = RootNode(
        children=(
            create_context(
                name='TestRoot',
                indent=2,
                other_children=(
                    create_context(
                        name='TestNameThing',
                        indent=4,
                        other_children=(
                            create_context(
                                name='TestDeeperThing',
                                indent=7,
                                other_children=(
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
        create_context(
            indent=2,
            name='TestRoot',
            other_children=(
                Test(
                    body=BlockOfCode(indent=7, body=" " * 7 + "code\n"),
                    indent=4,
                    name='test_name_thing_deeper_thing_foo_is_who',
                ),
            ),
        ),
    )
