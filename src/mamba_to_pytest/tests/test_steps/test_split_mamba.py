import io
import pytest
from more_itertools import one

from mamba_to_pytest.lines import LineOfCode, WithLine, BlankLine
from mamba_to_pytest.steps.split_mamba import split_mamba


def test_parse_code_line():
    line = '    code\n'
    node = one(list(split_mamba(io.StringIO(line))))
    assert node == LineOfCode(indent=4, line=line)


@pytest.mark.parametrize('line', ('\n', '    \n'))
def test_parse_blank_line(line):
    node = one(list(split_mamba(io.StringIO(line))))
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
    node = one(list(split_mamba(io.StringIO(line))))
    assert node == WithLine(indent=0, variable=variable, name=name, comment=comment, line=line, has_as_self=has_as_self)


def test_parse_irrelevant_with_line():
    line = 'with other:\n'
    node = one(list(split_mamba(io.StringIO(line))))
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
