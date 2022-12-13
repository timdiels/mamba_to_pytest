from __future__ import annotations

from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.convert_self_methods import convert_self_methods
from mamba_to_pytest.nodes import RootNode, TestContext, BlockOfCode, TestSetup, Fixture, Method, NodeBase, \
    TestTeardown, Test


def create_context(
        indent: int,
        other_children: tuple[NodeBase, ...],
        class_fixture: Fixture | None,
        method_fixture: Fixture | None,
) -> TestContext:
    return TestContext(
        indent=indent,
        name='context1',
        has_as_self=True,
        class_fixture=class_fixture,
        method_fixture=method_fixture,
        other_children=other_children,
    )


def test_convert_self_method_calls():
    """
    Convert in all relevant nodes with methods in current and ancestor contexts
    """
    # Given
    def create_block(indent: int) -> BlockOfCode:
        return BlockOfCode(indent=indent, body='  self.outer(x)\nself.inner(y)\n')

    def create_method(*, indent: int, name: str = 'f1', body: BlockOfCode) -> Method:
        return Method(indent=indent, body=body, name=name, tail='def f1(self, x):')

    root = RootNode(
        children=(
            create_context(
                indent=0,
                class_fixture=Fixture(
                    indent=1,
                    scope=TestScope.CLASS,
                    setup=TestSetup(indent=1, scope=TestScope.CLASS, body=create_block(indent=2)),
                    teardown=TestTeardown(indent=1, scope=TestScope.CLASS, body=create_block(indent=2)),
                    methods=()
                ),
                method_fixture=Fixture(
                    indent=1,
                    scope=TestScope.METHOD,
                    setup=TestSetup(indent=1, scope=TestScope.METHOD, body=create_block(indent=2)),
                    teardown=TestTeardown(indent=1, scope=TestScope.METHOD, body=create_block(indent=2)),
                    methods=(
                        create_method(indent=2, name='outer', body=create_block(indent=3)),
                    ),
                ),
                other_children=(
                    create_context(
                        indent=1,
                        class_fixture=Fixture(
                            indent=2,
                            scope=TestScope.CLASS,
                            setup=TestSetup(indent=2, scope=TestScope.CLASS, body=create_block(indent=3)),
                            teardown=TestTeardown(indent=2, scope=TestScope.CLASS, body=create_block(indent=3)),
                            methods=()
                        ),
                        method_fixture=Fixture(
                            indent=2,
                            scope=TestScope.METHOD,
                            setup=TestSetup(indent=2, scope=TestScope.METHOD, body=create_block(indent=3)),
                            teardown=TestTeardown(indent=2, scope=TestScope.METHOD, body=create_block(indent=3)),
                            methods=(
                                create_method(indent=3, name='inner', body=create_block(indent=4)),
                            ),
                        ),
                        other_children=(
                            create_block(3),
                        ),
                    ),
                    Test(indent=1, name='it', body=create_block(indent=2)),
                    create_block(indent=1),
                ),
            ),
        )
    )

    # When
    root = convert_self_methods(root)

    # Then method calls in code blocks for methods in scope are converted
    def create_converted_method(*, indent: int, name: str = 'f1', body: BlockOfCode) -> Method:
        return Method(indent=indent, body=body, name=name, tail='def f1(mamba, x):')

    def create_outer_block(indent: int) -> BlockOfCode:
        return BlockOfCode(indent=indent, body='  mamba.outer(mamba, x)\nself.inner(y)\n')

    def create_inner_block(indent: int) -> BlockOfCode:
        return BlockOfCode(indent=indent, body='  mamba.outer(mamba, x)\nmamba.inner(mamba, y)\n')

    outer_cls_block = BlockOfCode(indent=2, body='  mamba_cls.outer(mamba_cls, x)\nself.inner(y)\n')
    inner_cls_block = BlockOfCode(indent=3, body='  mamba_cls.outer(mamba_cls, x)\nmamba_cls.inner(mamba_cls, y)\n')

    assert root.children == (
        create_context(
            indent=0,
            class_fixture=Fixture(
                indent=1,
                scope=TestScope.CLASS,
                setup=TestSetup(indent=1, scope=TestScope.CLASS, body=outer_cls_block),
                teardown=TestTeardown(indent=1, scope=TestScope.CLASS, body=outer_cls_block),
                methods=()
            ),
            method_fixture=Fixture(
                indent=1,
                scope=TestScope.METHOD,
                setup=TestSetup(indent=1, scope=TestScope.METHOD, body=create_outer_block(indent=2)),
                teardown=TestTeardown(indent=1, scope=TestScope.METHOD, body=create_outer_block(indent=2)),
                methods=(
                    create_converted_method(indent=2, name='outer', body=create_outer_block(indent=3)),
                ),
            ),
            other_children=(
                create_context(
                    indent=1,
                    class_fixture=Fixture(
                        indent=2,
                        scope=TestScope.CLASS,
                        setup=TestSetup(indent=2, scope=TestScope.CLASS, body=inner_cls_block),
                        teardown=TestTeardown(indent=2, scope=TestScope.CLASS, body=inner_cls_block),
                        methods=()
                    ),
                    method_fixture=Fixture(
                        indent=2,
                        scope=TestScope.METHOD,
                        setup=TestSetup(indent=2, scope=TestScope.METHOD, body=create_inner_block(indent=3)),
                        teardown=TestTeardown(indent=2, scope=TestScope.METHOD, body=create_inner_block(indent=3)),
                        methods=(
                            create_converted_method(indent=3, name='inner', body=create_inner_block(indent=4)),
                        ),
                    ),
                    other_children=(
                        create_inner_block(3),
                    ),
                ),
                Test(indent=1, name='it', body=create_outer_block(indent=2)),
                create_outer_block(indent=1),
            ),
        ),
    )
