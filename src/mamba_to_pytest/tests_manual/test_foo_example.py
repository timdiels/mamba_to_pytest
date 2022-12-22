import pytest
# Tests should succeed before/after compilation, though note mamba ignores exceptions in after.* blocks.
# Before compilation can be run with: PYTHONPATH=tests/spec_helper mamba --format=documentation test_foo_spec.py
from unittest.mock import patch

# This import is removed

# No more self in file

# ClassCase
class TestIBecomeAClass:
    # ClassCase
    class TestAlsoAClass:
        # method_case
        def test_i_m_a_method_of_the_inner_class(self):
            # This is the body of the inner method
            pass
    def test_i_m_a_method_of_the_outer_class(self):
        # This is the body of the outer method
        pass

class TestDescribeIsAlsoAClass:
    def test_describe_can_be_nested_obligatory_test_method(self):
        # Obligatory body
        pass
        
class TestCanMixDescription:
    # The trailing comment should remain
    # or vice versa
    def test_with_describe_foo(self):
        # The name of this test method should be prefixed with test_, i.e. test_foo
        pass
        
class TestReplaceWeirdCharacters:
    def test_replace_weird_characters_in_methods_too(self, mamba):
        pass

# It creates mamba/mamba_cls fixture, regardless of presence of `as mamba`
class TestTopLevelFixture:
    class TestBeforeEachHasDefaultScope:
        @pytest.fixture(autouse=True)
        def mamba(self, mamba):
            mamba.x = 1
            yield mamba

        def test_has_correct_x(self, mamba):
            assert mamba.x == 1

    class TestAfterEachHasDefaultScope:
        @pytest.fixture(autouse=True)
        def mamba_other1(self):
            yield
            # there is a yield above this line
            # the next line has a trailing comment
            pass  # whooptidoo

        def test_obligatory_method(self):
            pass

    class TestBeforeAllHasClassScope:
        @pytest.fixture(autouse=True, scope="module")
        def mamba_cls(self, mamba_cls):
            mamba_cls = mamba_cls.copy()
            mamba_cls.x = 1
            yield mamba_cls

        def test_has_correct_x(self, mamba):
            assert mamba.x == 1

    class TestAfterAllHasClassScope:
        @pytest.fixture(autouse=True, scope="module")
        def mamba_other2(self):
            yield
            # there is a yield above this line
            # the next line has a trailing comment
            pass

        def test_obligatory_method(self):
            pass

    class TestBeforeAfterAreMergedCorrectly:
        @pytest.fixture(autouse=True, scope="module")
        def mamba_cls(self, mamba_cls):
            mamba_cls = mamba_cls.copy()
            # This ends up in cls fixture
            mamba_cls.y = 3
            yield mamba_cls
            # there is a yield above this line
            assert mamba_cls.y == 3

        @pytest.fixture(autouse=True)
        def mamba(self, mamba):
            # This ends up in func fixture
            mamba.x = 2
            yield mamba
            # there is a yield above this line
            assert mamba.x == 2

        # There is a fixture above this line for class and default scope
        def test_obligatory_method(self, mamba):
            assert mamba.x == 2
            assert mamba.y == 3

class TestSelfAtDeeperLevelAndCheckNestedBeforeAfter:
    class TestThisHasSelf:
        @pytest.fixture(autouse=True, scope="module")
        def mamba_other3(self):
            yield
            print('outer after all')

        @pytest.fixture(autouse=True)
        def mamba_other4(self):
            yield
            print('outer after each')

        class TestOuterAfterInnerBefore:
            @pytest.fixture(autouse=True, scope="module")
            def mamba_cls(self, mamba_cls):
                mamba_cls = mamba_cls.copy()
                mamba_cls.all = 'inner all'
                yield mamba_cls

            @pytest.fixture(autouse=True)
            def mamba(self, mamba):
                mamba.each = 'inner each'
                yield mamba

            def test_a_capital_d(self, mamba):
                assert mamba.all == 'inner all'
                assert mamba.each == 'inner each'

    class TestAlsoHasSelfNestedOtherWayAround:
        @pytest.fixture(autouse=True, scope="module")
        def mamba_cls(self, mamba_cls):
            mamba_cls = mamba_cls.copy()
            mamba_cls.all = 'outer all'
            yield mamba_cls

        @pytest.fixture(autouse=True)
        def mamba(self, mamba):
            mamba.each = 'outer each'
            yield mamba

        class TestOuterBeforeInnerAfter:
            @pytest.fixture(autouse=True, scope="module")
            def mamba_cls(self, mamba_cls):
                mamba_cls = mamba_cls.copy()
                yield mamba_cls
                assert mamba_cls.all == 'outer all'
            @pytest.fixture(autouse=True)
            def mamba(self, mamba):
                yield mamba
                assert mamba.each == 'outer each'

            def test_a_capital_d(self, mamba):
                assert mamba.all == 'outer all'
                assert mamba.each == 'outer each'

    class TestAlsoHasSelfInnerOverrides:
        @pytest.fixture(autouse=True, scope="module")
        def mamba_cls(self, mamba_cls):
            mamba_cls = mamba_cls.copy()
            mamba_cls.all = 'outer all'
            mamba_cls.all_not_overridden = 'outer all'
            yield mamba_cls

        @pytest.fixture(autouse=True)
        def mamba(self, mamba):
            mamba.each = 'outer each'
            mamba.each_not_overridden = 'outer each'
            yield mamba

        class TestOverriddenBefore:
            @pytest.fixture(autouse=True, scope="module")
            def mamba_cls(self, mamba_cls):
                mamba_cls = mamba_cls.copy()
                mamba_cls.all = 'inner all'
                yield mamba_cls

            @pytest.fixture(autouse=True)
            def mamba(self, mamba):
                mamba.each = 'inner each'
                yield mamba

            def test_a_capital_d(self, mamba):
                assert mamba.all == 'inner all'
                assert mamba.each == 'inner each'
                assert mamba.all_not_overridden == 'outer all'
                assert mamba.each_not_overridden == 'outer each'

        def test_unaffected_by_inner_before(self, mamba):
            assert mamba.all == 'outer all'
            assert mamba.each == 'outer each'


class TestExecutionOrderOfFixtures:
    @pytest.fixture(autouse=True, scope="module")
    def mamba_cls(self, mamba_cls):
        mamba_cls = mamba_cls.copy()
        print('outer cls')
        mamba_cls.a = 1
        yield mamba_cls

    @pytest.fixture(autouse=True)
    def mamba(self, mamba):
        print('outer meth')
        mamba.b = 2
        yield mamba

    # Check the execution order manually by looking at print statements
    def test_1(self, mamba):
        # Only these vars are in scope
        assert mamba.a == 1
        assert mamba.b == 2

    class TestDeeper:
        @pytest.fixture(autouse=True, scope="module")
        def mamba_cls(self, mamba_cls):
            mamba_cls = mamba_cls.copy()
            print('inner cls')
            mamba_cls.c = 3
            yield mamba_cls

        @pytest.fixture(autouse=True)
        def mamba(self, mamba):
            print('inner meth')
            mamba.d = 4
            yield mamba

        def test_1(self, mamba):
            assert mamba.a == 1
            assert mamba.b == 2
            assert mamba.c == 3
            assert mamba.d == 4

        def test_2(self, mamba):
            assert mamba.a == 1
            assert mamba.b == 2
            assert mamba.c == 3
            assert mamba.d == 4

    def test_2(self, mamba):
        # Only these vars are in scope
        assert mamba.a == 1
        assert mamba.b == 2


# No funny business with patch
def never_run_me():
    with open('f') as self:
        pass
    with patch('sys') as self:
        pass
    with patch('sys'
               ):
        pass


class TestFixtureOutsideAsSelfContextBecomesOtherFixture:
    @pytest.fixture(autouse=True, scope="module")
    def mamba_other5(self):
        my_all = 3

    @pytest.fixture(autouse=True)
    def mamba_other6(self):
        each = 3

    def test_1(self):
        ...


class TestFixtureInAsSelfContextWithoutSelfVarsBecomesOtherFixture:
    @pytest.fixture(autouse=True, scope="module")
    def mamba_other7(self):
        my_all = 3

    def test_1(self):
        ...


class DoNotChangeAnythingInHere:
    def __init__(self):
        self.is_still_self = True

    def test_does_not_raise(self):
        ...

    def is_ignored(self):
        ...


class TestHandleFunctionsWhichStartWithSelf:
    @pytest.fixture(autouse=True)
    def mamba(self, mamba):
        def add_thingy(mamba, i):
            mamba.thingies.append(mamba.factor * i)
            
        mamba.add_thingy = add_thingy
        mamba.factor = 3
        mamba.thingies = []
        yield mamba

    def ignore_without_self(i):
        """this func should not end up in the fixture"""

    def test_can_use_add(self, mamba):
        mamba.add_thingy(mamba, 2)
        assert mamba.thingies == [6]

    class TestUseCorrectMambaCopy:
        @pytest.fixture(autouse=True)
        def mamba_other8(self):
            ...  # another fixture to create another mamba copy

        def test_can_use_add(self, mamba):
            mamba.add_thingy(mamba, 3)
            assert mamba.thingies == [9]

    def test_isolated_from_previous_tests(self, mamba):
        assert not mamba.thingies


class TestHandleFunctionsWhichStartWithSelfEvenWithoutFixture:
    @pytest.fixture(autouse=True)
    def mamba(self, mamba):
        def can_call_me(mamba):
            ...
            
        def can_call_me_too(mamba):
            ...
            
        mamba.can_call_me = can_call_me
        mamba.can_call_me_too = can_call_me_too
        yield mamba

    def test_can_use_self_func(self, mamba):
        mamba.can_call_me(mamba)
        mamba.can_call_me_too(mamba)

        # Check that plain (mamba) is replaced too
        def f(x):
            x.can_call_me(x)  # although shortcoming, you manually need to pass x again here

        f(mamba)
