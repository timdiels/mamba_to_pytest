from functools import partial

from frozendict import frozendict

from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.convert_self_vars import convert_self_vars
from mamba_to_pytest.nodes import RootNode, TestContext, BlockOfCode, TestSetup, Fixture, Test, TestTeardown, NodeBase, \
    Method

IMPORT_PYTEST = BlockOfCode(indent=0, body='import pytest\n')


def create_fixture(indent: int, setup_body: str, setup_scope: TestScope = TestScope.METHOD):
    return Fixture(
        setup=TestSetup(
            indent=indent,
            body=BlockOfCode(indent=indent+1, body=setup_body),
            scope=setup_scope,
        ),
        teardown=None,
        scope=setup_scope,
        indent=indent,
        methods=(),
    )


def create_context(
        *,
        name: str = 'context1',
        indent: int = 0,
        has_as_self: bool = False,
        other_children: tuple[NodeBase, ...],
        class_fixture=None,
        method_fixture=None,
) -> TestContext:
    return TestContext(
        name=name,
        indent=indent,
        has_as_self=has_as_self,
        class_fixture=class_fixture,
        method_fixture=method_fixture,
        other_children=other_children,
    )


class TestConvertSelfVars:
    def test_replace_multiple_occurrences(self):
        context = create_context(
            indent=1,
            has_as_self=True,
            other_children=(
                BlockOfCode(body='foo self.x = bar\nself.z self.z(baaa)\nself.y me\nf(self)\n', indent=2),
            ),
        )
        root = RootNode(children=(context,))

        root = convert_self_vars(root)

        assert root.children == (
            create_context(
                indent=1,
                has_as_self=True,
                other_children=(
                    BlockOfCode(body='foo mamba.x = bar\nmamba.z mamba.z(baaa)\nmamba.y me\nf(mamba)\n', indent=2),
                )
            ),
        )

    def test_when_to_convert(self):
        # Given
        def create_block(indent: int):
            return BlockOfCode(body='self.x\n', indent=indent)
        root = RootNode(
            children=(
                create_context(
                    indent=1,
                    has_as_self=True,
                    other_children=(
                        create_block(2),
                        create_context(
                            indent=2,
                            has_as_self=False,
                            other_children=(create_block(3),),
                        ),
                    ),
                ),
                create_context(
                    indent=1,
                    has_as_self=False,
                    other_children=(create_block(2),),
                ),
            )
        )

        # When
        root = convert_self_vars(root)

        # Then
        def create_converted_block(indent: int):
            return BlockOfCode(body='mamba.x\n', indent=indent)
        assert root.children == (
            create_context(
                indent=1,
                # This starts a self scope
                has_as_self=True,
                other_children=(
                    # meaning we convert self vars
                    create_converted_block(2),
                    # considering an ancestor context has self, this context is also in the self scope regardless of
                    # its own has_as_self
                    create_context(
                        indent=2,
                        has_as_self=False,
                        other_children=(create_converted_block(3),),
                    ),
                ),
            ),
            # when not in scope, do not convert self vars
            create_context(
                indent=1,
                has_as_self=False,
                other_children=(create_block(2),),
            ),
        )

    def test_convert_test_node(self):
        block = BlockOfCode(indent=4, body='    self.x\n')
        context = create_context(
            indent=0,
            has_as_self=True,
            other_children=(Test(indent=2, name='test_thing', body=block),)
        )
        root = RootNode(children=(context,))

        root = convert_self_vars(root)

        assert root.children == (
            create_context(
                indent=0,
                has_as_self=True,
                other_children=(BlockOfCode(body='  def test_thing(self, mamba):\n    mamba.x\n', indent=2),)
            ),
        )

    class TestConvertFixture:
        @staticmethod
        def create_root(scope: TestScope, has_as_self=False) -> RootNode:
            fixture = Fixture(
                setup=TestSetup(indent=2, body=BlockOfCode(indent=4, body='    self.setup = 3\n'), scope=scope),
                teardown=TestTeardown(indent=2, body=BlockOfCode(indent=4, body='    teardown\n'), scope=scope),
                scope=scope,
                indent=2,
                methods=(),
            )
            if scope == TestScope.CLASS:
                kwargs = {'class_fixture': fixture}
            else:
                kwargs = {'method_fixture': fixture}
            return RootNode(
                children=(
                    create_context(
                        indent=0,
                        name='TestClass',
                        has_as_self=has_as_self,
                        other_children=(),
                        **kwargs,
                    ),
                )
            )

        def test_class_scope(self):
            root = self.create_root(TestScope.CLASS)
            root = convert_self_vars(root)
            assert f'  @pytest.fixture(autouse=True, scope="class")\n' in root.children[1].children[0].body

        def test_method_scope(self):
            root = self.create_root(TestScope.METHOD)
            root = convert_self_vars(root)
            assert f'  @pytest.fixture(autouse=True)\n' in root.children[1].children[0].body

        def test_with_self_vars(self):
            root = self.create_root(TestScope.METHOD, has_as_self=True)
            root = convert_self_vars(root)
            assert root.children == (
                IMPORT_PYTEST,
                create_context(
                    indent=0,
                    name='TestClass',
                    has_as_self=True,
                    other_children=(
                        BlockOfCode(
                            body=(
                                f'  @pytest.fixture(autouse=True)\n'
                                f'  def mamba(self, mamba):\n'
                                f'    mamba = mamba.copy()\n'
                                f'    mamba.setup = 3\n'
                                f'    yield mamba\n'
                                f'    teardown\n'
                            ),
                            indent=2,
                        ),
                    )
                ),
            )

        def test_without_self_vars(self):
            root = self.create_root(TestScope.METHOD, has_as_self=False)
            root = convert_self_vars(root)
            assert root.children == (
                IMPORT_PYTEST,
                create_context(
                    indent=0,
                    name='TestClass',
                    has_as_self=False,
                    other_children=(
                        BlockOfCode(
                            # Our given is a bit unrealistic as self should never appear in a fixture outside a self
                            # scope unless in a class
                            body=(
                                f'  @pytest.fixture(autouse=True)\n'
                                f'  def mamba_other1(self):\n'
                                f'    self.setup = 3\n'
                                f'    yield\n'
                                f'    teardown\n'
                            ),
                            indent=2,
                        ),
                    )
                ),
            )

        def test_with_only_methods(self):
            context = create_context(
                indent=0,
                class_fixture=None,
                has_as_self=True,
                method_fixture=Fixture(
                    setup=None,
                    teardown=None,
                    methods=(
                        Method(
                            indent=4,
                            name='add_thingy',
                            body=BlockOfCode(indent=6, body=' ' * 6 + 'self.y = x\n\n'),
                            tail='def add_thingy(mamba, x):\n',
                        ),
                    ),
                    scope=TestScope.METHOD,
                    indent=2,
                ),
                other_children=(),
            )
            root = RootNode(children=(context,))

            root = convert_self_vars(root)

            assert root.children == (
                IMPORT_PYTEST,
                create_context(
                    indent=0,
                    has_as_self=True,
                    class_fixture=None,
                    method_fixture=None,
                    other_children=(
                        BlockOfCode(
                            body=(
                                '  @pytest.fixture(autouse=True)\n'
                                '  def mamba(self, mamba):\n'
                                '    def add_thingy(mamba, x):\n'
                                '      mamba.y = x\n\n'
                                '    mamba = mamba.copy()\n'
                                '    mamba.add_thingy = add_thingy\n'
                                '    yield mamba\n\n'
                            ),
                            indent=2,
                        ),
                    )
                ),
            )
