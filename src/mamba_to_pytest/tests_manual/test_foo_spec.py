# Tests should succeed before/after compilation, though note mamba ignores exceptions in after.* blocks.
# Before compilation can be run with: PYTHONPATH=tests/spec_helper mamba --format=documentation test_foo_spec.py
from unittest.mock import patch

# This import is removed
from mamba import description, it, describe, context, before, after

# No more self in file

# ClassCase
with description("I become a class"):
    # ClassCase
    with description("Also a class"):
        # method_case
        with it("I'm a method of the inner class"):
            # This is the body of the inner method
            pass
    with it("I'm a method of the outer class"):
        # This is the body of the outer method
        pass

with describe("Describe is also a class"):
    with describe("Describe can be nested"):
        with it("Obligatory test method"):
            # Obligatory body
            pass

with description("Can mix description"):
    # The trailing comment should remain
    with describe("With describe"):  # or vice versa
        with it('foo'):
            # The name of this test method should be prefixed with test_, i.e. test_foo
            pass

with description("Replace weird characters ~!@#$%^^&**()_+{}[]:<>?|,./\"\\'"):
    with it("Replace weird characters in methods too ~!@#$%^^&**()_+{}[]:<>?|,./\"\\'"):
        pass

# `as self` becomes a mamba and mamba_cls fixture
with description("top level fixture") as self:
    with context("before each has default scope"):
        with before.each:
            self.x = 1

        with it("has correct x"):
            assert self.x == 1

    with context("after each has default scope"):
        with after.each:
            # there is a yield above this line
            # the next line has a trailing comment
            pass  # whooptidoo

        with it("obligatory method"):
            pass

    with context("before all has class scope"):
        with before.all:
            self.x = 1

        with it("has correct x"):
            assert self.x == 1

    with context("after all has class scope"):
        with after.all:
            # there is a yield above this line
            # the next line has a trailing comment
            pass

        with it("obligatory method"):
            pass

    with context("before/after are merged correctly"):
        # There is a fixture above this line for class and default scope
        with it("obligatory method"):
            assert self.x == 2
            assert self.y == 3

        with after.each:
            # there is a yield above this line
            assert self.x == 2

        with before.each:
            # This ends up in func fixture
            self.x = 2

        with after.all:
            # there is a yield above this line
            assert self.y == 3

        with before.all:
            # This ends up in cls fixture
            self.y = 3

with description("self at deeper level and check nested before/after"):
    with describe("this has self") as self:
        with after.all:
            print('outer after all')

        with after.each:
            print('outer after each')

        with context('outer after inner before'):
            with it("a capital D"):
                assert self.all == 'inner all'
                assert self.each == 'inner each'

            with before.all:
                self.all = 'inner all'

            with before.each:
                self.each = 'inner each'

    with describe("also has self, nested other way around") as self:
        with before.all:
            self.all = 'outer all'
        with before.each:
            self.each = 'outer each'

        with context('outer before inner after'):
            with it("a capital D"):
                assert self.all == 'outer all'
                assert self.each == 'outer each'

            with after.all:
                assert self.all == 'outer all'
            with after.each:
                assert self.each == 'outer each'

    with describe("also has self, inner overrides") as self:
        with before.all:
            self.all = 'outer all'
            self.all_not_overridden = 'outer all'
        with before.each:
            self.each = 'outer each'
            self.each_not_overridden = 'outer each'

        with context('overridden before'):
            with it("a capital D"):
                assert self.all == 'inner all'
                assert self.each == 'inner each'
                assert self.all_not_overridden == 'outer all'
                assert self.each_not_overridden == 'outer each'

            with before.all:
                self.all = 'inner all'
            with before.each:
                self.each = 'inner each'

        with it("unaffected by inner before"):
            assert self.all == 'outer all'
            assert self.each == 'outer each'


with context('execution order of fixtures') as self:
    # Check the execution order manually by looking at print statements
    with before.all:
        print('outer cls')
        self.a = 1

    with before.each:
        print('outer meth')
        self.b = 2

    with it('1'):
        # Only these vars are in scope
        assert self.a == 1
        assert self.b == 2

    with context('deeper'):
        with before.all:
            print('inner cls')
            self.c = 3

        with before.each:
            print('inner meth')
            self.d = 4

        with it('1'):
            assert self.a == 1
            assert self.b == 2
            assert self.c == 3
            assert self.d == 4

        with it('2'):
            assert self.a == 1
            assert self.b == 2
            assert self.c == 3
            assert self.d == 4

    with it('2'):
        # Only these vars are in scope
        assert self.a == 1
        assert self.b == 2


# No funny business with patch
def never_run_me():
    with open('f') as self:
        pass
    with patch('sys') as self:
        pass
    with patch('sys'
               ):
        pass


with description('fixture outside as-self context becomes other fixture'):
    with before.all:
        my_all = 3

    with before.each:
        each = 3

    with it('1'):
        ...


with description('fixture in as-self context without self vars becomes other fixture') as self:
    with before.all:
        my_all = 3

    with it('1'):
        ...


class DoNotChangeAnythingInHere:
    def __init__(self):
        self.is_still_self = True

    def test_does_not_raise(self):
        ...

    def is_ignored(self):
        ...


with context('handle functions which start with self') as self:
    def add_thingy(self, i):
        self.thingies.append(self.factor * i)

    def ignore_without_self(i):
        """this func should not end up in the fixture"""

    with before.each:
        self.factor = 3
        self.thingies = []

    with it('can use add'):
        self.add_thingy(2)
        assert self.thingies == [6]

    with context('use correct mamba copy'):
        with before.each:
            ...  # another fixture to create another mamba copy

        with it('can use add'):
            self.add_thingy(3)
            assert self.thingies == [9]

    with it('isolated from previous tests'):
        assert not self.thingies


with context('handle functions which start with self even without fixture') as self:
    def can_call_me(self):
        ...

    def can_call_me_too(self):
        ...

    with it('can use self func'):
        self.can_call_me()
        self.can_call_me_too()

        # Check that plain (self) is replaced too
        def f(x):
            x.can_call_me(x)  # although shortcoming, you manually need to pass x again here

        f(self)
