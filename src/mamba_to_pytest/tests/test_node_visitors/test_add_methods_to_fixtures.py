from __future__ import annotations

from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.add_methods_to_fixtures import add_methods_to_fixtures
from mamba_to_pytest.nodes import RootNode, TestContext, BlockOfCode, TestSetup, Fixture, Method, NodeBase


def create_block(indent: int) -> BlockOfCode:
    return BlockOfCode(indent=indent, body=" " * indent + "code\n")


def create_context(
        indent: int,
        other_children: tuple[NodeBase, ...],
        class_fixture: Fixture | None,
        method_fixture: Fixture | None,
) -> TestContext:
    return TestContext(
        indent=indent,
        other_children=other_children,
        name='context1',
        class_fixture=class_fixture,
        method_fixture=method_fixture,
    )


def create_method(*, indent: int, name: str = 'f1', body: BlockOfCode) -> Method:
    return Method(indent=indent, body=body, name=name, tail='tail\n')


def create_fixture(indent: int, scope: TestScope, body: BlockOfCode, methods: tuple[Method, ...] = ()) -> Fixture:
    return Fixture(
        setup=TestSetup(
            indent=indent,
            scope=scope,
            body=body,
        ),
        teardown=None,
        methods=methods,
        scope=scope,
        indent=indent,
    )


def test_add_methods_to_method_fixture():
    # Given some class fixtures, they should have no effect on the visitor
    top_class_fixture = create_fixture(indent=1, scope=TestScope.CLASS, body=create_block(indent=2))
    deep_class_fixture = create_fixture(indent=2, scope=TestScope.CLASS, body=create_block(indent=3))

    root = RootNode(
        children=(
            create_context(
                indent=0,
                class_fixture=top_class_fixture,
                method_fixture=create_fixture(indent=1, scope=TestScope.METHOD, body=create_block(indent=3)),
                other_children=(
                    create_block(indent=1),
                    create_method(indent=1, name='top1', body=create_block(indent=2)),
                    create_context(
                        indent=1,
                        class_fixture=deep_class_fixture,
                        method_fixture=create_fixture(indent=2, scope=TestScope.METHOD, body=create_block(indent=5)),
                        other_children=(
                            create_method(indent=2, name='deep1', body=create_block(indent=3)),
                            create_block(indent=2),
                            create_method(indent=2, name='deep2', body=create_block(indent=12)),
                        ),
                    ),
                    create_method(indent=1, name='top2', body=create_block(indent=10)),
                ),
            ),
        )
    )

    # When
    root = add_methods_to_fixtures(root)

    # Then
    top_methods = (
        # method.indent becomes the body indent of the method fixture and the method body is method.indent + 4
        create_method(indent=3, name='top1', body=create_block(indent=7)),
        create_method(indent=3, name='top2', body=create_block(indent=7)),
    )
    deep_methods = (
        # same for the deeper context
        create_method(indent=5, name='deep1', body=create_block(indent=9)),
        create_method(indent=5, name='deep2', body=create_block(indent=9)),
    )
    assert root.children == (
        create_context(
            indent=0,
            class_fixture=top_class_fixture,
            # methods are added to the method fixture
            method_fixture=create_fixture(
                indent=1, scope=TestScope.METHOD, body=create_block(indent=3), methods=top_methods
            ),
            other_children=(
                # methods are no longer children, everything else remains unchanged
                create_block(indent=1),
                create_context(
                    indent=1,
                    class_fixture=deep_class_fixture,
                    method_fixture=create_fixture(
                        indent=2, scope=TestScope.METHOD, body=create_block(indent=5), methods=deep_methods
                    ),
                    other_children=(
                        create_block(indent=2),
                    ),
                ),
            ),
        ),
    )


def test_create_fixture_if_missing():
    class_fixture = create_fixture(indent=1, scope=TestScope.CLASS, body=create_block(indent=2))
    root = RootNode(
        children=(
            create_context(
                indent=0,
                # This might as well be None, just checking that class fixtures have no effect on this visitor
                class_fixture=class_fixture,
                # What matters is that this is None, so will need to be created as we have a method child
                method_fixture=None,
                other_children=(
                    create_method(indent=2, body=create_block(indent=3)),
                ),
            ),
        )
    )

    root = add_methods_to_fixtures(root)

    assert root.children == (
        create_context(
            indent=0,
            class_fixture=class_fixture,
            method_fixture=Fixture(
                setup=None,
                teardown=None,
                scope=TestScope.METHOD,
                indent=2,  # original indent of the method
                methods=(
                    create_method(
                        # indent of the fixture + 4
                        indent=6,
                        # indent of the method + 4
                        body=create_block(indent=10),
                    ),
                ),
            ),
            other_children=(),
        ),
    )
