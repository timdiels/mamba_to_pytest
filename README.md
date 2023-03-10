Converts mamba tests to pytest. Usually some manual fixes are required, but it's a good starting point. To verify things went well: compare the number of tests ran, make sure they pass, compare test coverage.

To see it in action, compare [this converted file](./src/mamba_to_pytest/tests_manual/test_foo_example.py) to
[its mamba source](./src/mamba_to_pytest/tests_manual/test_foo_spec.py).

This project is made available under the MIT license. Developed at [ONTOFORCE](https://www.ontoforce.com/),
they kindly let me share it.


## Usage
Install with:

    pip install -r requirements.txt
    pip install -e .

Run with:

    mamba_to_pytest test_1_spec.py test_spec.py ...

The original file is renamed to `disabled_*_disabled.py` so it's no longer picked up by your test runner. You can still
make changes to the disabled file and convert it again if necessary.

Converting entire directories:

    find directory1 directory2 ... -name 'test_*_spec.py' -exec mamba_to_pytest '{}' \+ 
    find directory1 directory2 ... -name 'disabled_*_disabled.py' -exec mamba_to_pytest '{}' \+ 

If the command lists failures, you'll have to make adjustments to the mamba file and rerun it (or contribute a PR to
adjust it automatically). If the tests fail, you can adjust either the mamba file or fix it in the pytest file.


### Manual fixes after conversion
- Copy [this conftest.py](./src/mamba_to_pytest/tests_manual/conftest.py) to the root of any tests which use the mamba
  pytest fixture.


### Manual fixes in mamba files
These will usually result in a 'random' error during conversion or will cause your tests to fail or not run
at all (which is why you should check test count before/after conversion). You don't need to go over your files
manually up front, it's quicker to discover and fix these problems in mamba code by trying to convert them and run the
converted tests.

#### Multiline strings
The converter gets confused by multiline strings; this will usually result in a 'random' error, so you don't need to
hunt for these. It does not realise that the dedented part is still part of the same code block.

```python
    indented_var = '''
dedented str
'''
```

Fix like so:

```python
    indented_var = (
        '\n'
        'dedented str\n'
    )
```

#### Multiline self methods/functions
Multiline method headings cause it to miss the actual method body. In this example it thinks `x):` is the body and
`...` is some code following the method.

```python
def longer_method_name(self,
                       x):
    ...
```

Fix by making it a single line heading:

```python
def longer_method_name(self, x):
    ...
```


#### Forgot `as self`
If the converter creates a mamba_other fixture or does not replace `self` in places where it should, make sure that one
of the parent contexts (`with context` or `description`, ...) has an `as self`. The converter intentionally leaves `self`
alone otherwise; it's surprising that this worked in mamba to begin with.


## Quirks / shortcomings
Other than the ones listed in manual fixes:

- It's very easy to forget `as self` on a with line that the converter just assumes it's implicitly present. This is
  fine so long as you do not use `self` as a regular variable outside a class or method (in a class), otherwise those
  would be renamed to `mamba`.
- before.all is converted to module scoped fixtures as class scoped fixtures have a tendency to be rerun each time the
  pytest runner switches to a test at a different nesting level. E.g.

  ```python
  with context(...) as self:
    with before.all:
        ...
    with it('1'):
        ...
    with context(...):
        with it('2'):
            ...
    with it('3'):
        ...
    with it('4'):
        ...
  ```
  
  Mamba would run the before.all once and runs tests breadth first, i.e. 1, 3, 4, 2.
  pytest Runs depth first, i.e. 1, 2, 3, 4 and runs the before.all before test 1, and 3.

## Design of the converter
### Approaches considered
The approach taken is an adhoc parser.

#### Use ast.parse/unparse?
This is what mamba uses internally, this potentially would have allowed reusing some of mamba???s code to make sense of
the code in order to rewrite it to pytest instead of mamba???s usual output. Could have modified the mamba source code to
make those changes.

But `unparse(parse(x))` loses comments, formatting and `unparse` may even fail for complex ASTs according to python docs.

#### Prepend each file with imports which implement mamba without magic?
Mamba code is syntactically valid, I briefly considered reimplementing mamba describe, it, ??? using proper context managers in hopes of PyCharm being able to make sense of it.

But the code would still look like mamba, with its `self` var leading to smelly code.

#### Write an adhoc parser
Parse just enough, or maybe even a bit less, for the bits of the code that we need to change. Hopefully this can understand most of the files, the remainder can be converted manually.


### mamba facts
- description, describe, context can be treated as equivalent when converting
- before.all, before.each, after.all, after.each have a compatible execution order as pytest fixtures (function and
  module scope). The only difference is that pytest runs tests depth first whereas mamba is breadth first. In the
  following example pytest will run the class fixture once for test1, and once more after TestsDeeper. The equivalent mamba code would run the fixture once, run test 1, 2, 3 and only then would it run the deeper tests. But see also the before/after.all shortcoming above.

  ```python
  class Tests:
      @pytest.fixture(scope='class')
      def my_fixture(self):
          ...

      def test1(self): ...
      
      class TestsDeeper:
          def test_deep(self): ...

      def test2(self): ...
      def test3(self): ...
  ```

- All mamba files end in _spec.py