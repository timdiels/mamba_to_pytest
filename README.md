Converts mamba tests to pytest. Usually some manual fixes are required, but it's a good starting point. To verify things went well: compare the number of tests ran, make sure they pass, compare test coverage.

This project is made available under the MIT license.

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
- Prefix test directories with `test_`
- Create a `conftest.py` (copy tests_manual/conftest.py) at the root of any tests which use the mamba pytest fixture


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
