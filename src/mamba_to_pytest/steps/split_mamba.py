from __future__ import annotations
import typing as t

from mamba_to_pytest.constants import MAMBA_IMPORT_PATTERN, WITH_START_PATTERN, CLASS_PATTERN, METHOD_START_PATTERN, \
    LINE_PATTERN, WITH_PATTERN
from mamba_to_pytest.lines import WithLine, LineOfCode, CodelessLine, ClassHeading, MethodHeading


def split_mamba(mamba_input: t.TextIO) -> t.Iterable[LineOfCode | CodelessLine]:
    for line in mamba_input.readlines():
        line = line.rstrip('\n')
        is_blank_line = not line or line.isspace()
        if is_blank_line:
            yield CodelessLine(line=line + '\n')
        elif line.startswith('def test_'):
            raise Exception(f"Function needs to be renamed as pytest will think it's a test:\n{line}")
        else:
            indent, tail = _parse_line(line)

            if MAMBA_IMPORT_PATTERN.match(tail):
                continue

            if tail.startswith('#'):
                yield CodelessLine(line + '\n')
            elif WITH_START_PATTERN.match(tail):
                yield _parse_a_with_line(indent, tail, line)
            elif CLASS_PATTERN.match(tail):
                yield ClassHeading(indent=indent, line=line + '\n')
            elif match := METHOD_START_PATTERN.match(tail):
                name = match.group(1)
                yield MethodHeading(indent=indent, name=name, line=line + '\n')
            else:
                yield LineOfCode(indent=indent, line=line + '\n')


def _parse_line(line: str) -> tuple[int, str]:
    match = LINE_PATTERN.match(line)
    assert match
    leading_spaces, tail = match.groups()
    assert not tail.startswith('\t')
    indent = len(leading_spaces)
    return indent, tail


def _parse_a_with_line(indent: int, tail: str, line: str) -> WithLine:
    match = WITH_PATTERN.match(tail)
    assert match, f'Cannot convert this with-line automatically, please simplify it first:\n{line}'
    return WithLine(
        variable=match.group(1).replace('_', '.'),
        name=match.group(2),
        comment=match.group(3),
        line=line + '\n',
        indent=indent,
    )