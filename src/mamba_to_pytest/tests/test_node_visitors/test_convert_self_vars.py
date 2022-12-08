from frozendict import frozendict

from mamba_to_pytest.constants import TestScope
from mamba_to_pytest.node_visitors.convert_self_vars import _CollectSelfVars, _ConvertSelfVars, \
    _VarScopes
from mamba_to_pytest.nodes import RootNode, TestContext, BlockOfCode, TestSetup, Fixture, Test, TestTeardown

IMPORT_PYTEST = BlockOfCode(indent=0, body='import pytest\n')


def collect_self_vars(root: RootNode) -> _VarScopes:
    return root.accept(_CollectSelfVars())


def _convert_self_vars(root: RootNode, var_scopes: _VarScopes) -> RootNode:
    return root.accept(_ConvertSelfVars(var_scopes))


def create_fixture(indent: int, setup_body: str, setup_scope: TestScope = TestScope.METHOD):
    return Fixture(
        setup=TestSetup(
            indent=indent,
            body=BlockOfCode(indent=indent+1, body=setup_body),
            scope=setup_scope,
        ),
        teardown=None
    )


class TestCollectSelfVars:
    def test_ignore_vars_outside_context_with_self(self):
        def create_ignore_me_block(indent: int) -> BlockOfCode:
            return BlockOfCode(indent=indent, body='self.ignore_me = 3\n')

        root = RootNode(
            children=(
                create_ignore_me_block(indent=1),
                TestContext(
                    indent=1,
                    name='TestName',
                    has_as_self=False,
                    children=(create_ignore_me_block(indent=2),)
                ),
            ),
        )

        var_scopes = collect_self_vars(root)

        assert not var_scopes

    def test_ignore_non_assignment(self):
        context = TestContext(
            indent=1,
            name='TestName',
            has_as_self=True,
            children=(BlockOfCode(indent=2, body='self.ignore_me # =\nself.ignore_me_too == 3'),)
        )
        root = RootNode(children=(context,))

        var_scopes = collect_self_vars(root)

        assert not var_scopes

    def test_collect_assignments_below_context_with_self(self):
        context = TestContext(
            indent=1,
            name='TestName',
            has_as_self=True,
            children=(
                # Should check for assignments in all descendants
                TestContext(
                    indent=2,
                    name='TestName2',
                    has_as_self=False,
                    children=(
                        create_fixture(
                            indent=3,
                            # This also checks the assignment parsing
                            setup_body='self.x = 3\nself.multiline_works = 4\nself.method=f(oijoi)',
                        ),
                    ),
                ),
                # (Other nodes should not contain self assignments)
            )
        )
        root = RootNode(children=(context,))

        var_scopes = collect_self_vars(root)

        assert var_scopes == {context: frozenset({'self.x', 'self.multiline_works', 'self.method'})}

    def test_multiple_scopes(self):
        context1 = TestContext(
            indent=1,
            name='TestName',
            has_as_self=True,
            children=(create_fixture(indent=2, setup_body='self.x = 3\n'),)
        )
        context2 = TestContext(
            indent=1,
            name='TestName2',
            has_as_self=True,
            children=(create_fixture(indent=2, setup_body='self.y = 3\n'),)
        )
        root = RootNode(children=(context1, context2))

        var_scopes = collect_self_vars(root)

        assert frozendict(var_scopes) == frozendict({
            context1: frozenset({"self.x"}),
            context2: frozenset({"self.y"}),
        })

    def test_nested_vars(self):
        context = TestContext(
            indent=1,
            name='TestName',
            has_as_self=True,
            children=(
                TestSetup(
                    body=BlockOfCode(indent=3, body='self.x = 1\nself.y = 2'),
                    scope=TestScope.METHOD,
                    indent=2,
                ),
                TestContext(
                    indent=2,
                    name='TestName2',
                    has_as_self=False,
                    children=(
                        TestSetup(
                            indent=3,
                            body=BlockOfCode(indent=4, body='self.x = 3\n self.z = 1\n'),
                            scope=TestScope.CLASS,
                        ),
                    ),
                ),
            )
        )
        root = RootNode(children=(context,))

        var_scopes = collect_self_vars(root)

        assert var_scopes == {context: frozenset({'self.x', 'self.y', 'self.z'})}


class TestConvertSelfVars:
    def test_replace_multiple_occurrences(self):
        context = TestContext(
            indent=1,
            name='TestName',
            has_as_self=False,  # no longer matters
            children=(
                BlockOfCode(body='foo self.x = bar\nself.z self.z(baaa)\nself.y me\n', indent=2),
            ),
        )
        var_scopes = {context: frozenset({'self.x', 'self.y', 'self.z'})}
        root = RootNode(children=(context,))

        root = _convert_self_vars(root, var_scopes)

        assert root.children == (
            TestContext(
                indent=1,
                name='TestName',
                has_as_self=False,
                children=(
                    BlockOfCode(body='foo mamba.x = bar\nmamba.z mamba.z(baaa)\nmamba.y me\n', indent=2),
                )
            ),
        )

    def test_multiple_contexts(self):
        # Given
        def create_context(name, body):
            return TestContext(
                indent=1,
                name=name,
                has_as_self=False,
                children=(BlockOfCode(body=body, indent=2),),
            )

        contexts = tuple(create_context(f'TestName{i}', 'self.x self.y\n') for i in range(3))
        var_scopes = {
            contexts[0]: frozenset({'self.x'}),
            contexts[1]: frozenset({'self.y'}),
        }
        root = RootNode(children=contexts)

        # When
        root = _convert_self_vars(root, var_scopes)

        # Then
        assert root.children == (
            create_context('TestName0', 'mamba.x self.y\n'),
            create_context('TestName1', 'self.x mamba.y\n'),
            create_context('TestName2', 'self.x self.y\n'),
        )

    def test_convert_test_node(self):
        block = BlockOfCode(indent=4, body='    self.x\n')
        context = TestContext(
            indent=0,
            name='TestClass',
            has_as_self=False,
            children=(Test(indent=2, name='test_thing', body=block),)
        )
        var_scopes = {context: frozenset({'self.x'})}
        root = RootNode(children=(context,))

        root = _convert_self_vars(root, var_scopes)

        assert root.children == (
            TestContext(
                indent=0,
                name='TestClass',
                has_as_self=False,
                children=(BlockOfCode(body='  def test_thing(self, mamba):\n    mamba.x\n', indent=2),)
            ),
        )

    class TestConvertFixture:
        @staticmethod
        def create_root(scope: TestScope, has_self_vars=False) -> tuple[RootNode, _VarScopes]:
            context = TestContext(
                indent=0,
                name='TestClass',
                has_as_self=False,
                children=(
                    Fixture(
                        setup=TestSetup(indent=2, body=BlockOfCode(indent=4, body='    self.setup = 3\n'), scope=scope),
                        teardown=TestTeardown(indent=2, body=BlockOfCode(indent=4, body='    teardown\n'), scope=scope),
                    ),
                ),
            )

            if has_self_vars:
                var_scopes = {context: frozenset({'self.setup'})}
            else:
                var_scopes = {}

            return RootNode(children=(context,)), var_scopes

        def test_class_scope(self):
            root, var_scopes = self.create_root(TestScope.CLASS)
            root = _convert_self_vars(root, var_scopes)
            assert f'  @pytest.fixture(autouse=True, scope="class")\n' in root.children[1].children[0].body

        def test_method_scope(self):
            root, var_scopes = self.create_root(TestScope.METHOD)
            root = _convert_self_vars(root, var_scopes)
            assert f'  @pytest.fixture(autouse=True)\n' in root.children[1].children[0].body

        def test_with_self_vars(self):
            root, var_scopes = self.create_root(TestScope.METHOD, has_self_vars=True)
            root = _convert_self_vars(root, var_scopes)
            assert root.children == (
                IMPORT_PYTEST,
                TestContext(
                    indent=0,
                    name='TestClass',
                    has_as_self=False,
                    children=(
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
            root, var_scopes = self.create_root(TestScope.METHOD, has_self_vars=False)
            root = _convert_self_vars(root, var_scopes)
            assert root.children == (
                IMPORT_PYTEST,
                TestContext(
                    indent=0,
                    name='TestClass',
                    has_as_self=False,
                    children=(
                        BlockOfCode(
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
