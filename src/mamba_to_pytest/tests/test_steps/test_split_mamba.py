import io
import pytest
from more_itertools import one

from mamba_to_pytest.lines import LineOfCode, WithLine, BlankLine, ClassHeading, MethodHeading
from mamba_to_pytest.steps.split_mamba import split_mamba


@pytest.mark.parametrize(
    'line,cls',
    (
        ('    code\n', LineOfCode),
        ('    class Foo:\n', ClassHeading),
        ('    class  Foo:\n', ClassHeading),
        ('    class  Foo:  # comment\n', ClassHeading),
        ('    class Foo\n', ClassHeading),
        ('    def foo(self):\n', MethodHeading),
        ('    def foo(self, x):\n', MethodHeading),
        ('    def foo(self,\n', MethodHeading),
        ('    def foo(self:\n', MethodHeading),
        ('    def foo(self \n', MethodHeading),
        ('    def foo(self\n', MethodHeading),
        ('    def  foo(self\n', MethodHeading),
        ('    def foo( self\n', MethodHeading),
        ('    def foo(self # comment\n', MethodHeading),
        ('    def foo(not_self\n', LineOfCode),
        ('    def foo(self_not\n', LineOfCode),
    ),
)
def test_simple_lines(line: str, cls):
    actual = one(split_mamba(io.StringIO(line)))
    assert not isinstance(actual, BlankLine)  # sooth mypy
    assert actual.indent == 4
    assert actual.line == line
    assert actual.__class__ == cls


@pytest.mark.parametrize('line', ('\n', '    \n'))
def test_parse_blank_line(line):
    node = one(split_mamba(io.StringIO(line)))
    assert node == BlankLine(line=line)


@pytest.mark.parametrize(
    'line,variable,name,comment,has_as_self',
    (
        ('with it:\n', 'it', None, None, False),
        ('with before.all:  # comment\n', 'before.all', None, '# comment', False),
        ('with description("my #. desc"):\n', 'description', "my #. desc", None, False),
        ('with description("my #. desc") as self:\n', 'description', "my #. desc", None, True),
    )
)
def test_parse_a_with_line(line, variable, name, comment, has_as_self):
    node = one(split_mamba(io.StringIO(line)))
    assert node == WithLine(indent=0, variable=variable, name=name, comment=comment, line=line, has_as_self=has_as_self)


def test_parse_irrelevant_with_line():
    line = 'with other:\n'
    node = one(split_mamba(io.StringIO(line)))
    assert node == LineOfCode(indent=0, line=line)

@pytest.mark.parametrize(
    'line,ignore',
    (
        ('import mamba', True),
        ('import mambar', False),
        ('from mamba', True),
        ('from mamba import', True),
        ('from mambar', False),
    ),
)
def test_ignore_mamba_import(line: str, ignore: bool):
    lines = list(split_mamba(io.StringIO(line)))
    if ignore:
        assert not lines
    else:
        assert len(lines) == 1
