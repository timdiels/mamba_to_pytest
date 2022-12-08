from __future__ import annotations
import re
import typing as t

from mamba_to_pytest.lines import WithLine, LineOfCode, BlankLine

_LINE_PATTERN = re.compile(r'^( *)([^ ].*)?$')
_MAMBA_IMPORT_PATTERN = re.compile(r'''^(from|import) mamba(\s|$)''')

_WITH_START = r'''^with\s+(description|context|describe|it|(?:before|after)[._](?:each|all))\s*'''
_WITH_START_PATTERN = re.compile(_WITH_START)
_WITH_PATTERN = re.compile(_WITH_START + r'''(?:[(]['"](.*)['"][)])?( as self)?:\s*(#.*)?$''')


def split_mamba(mamba_input: t.TextIO) -> t.Iterable[LineOfCode | BlankLine]:
    for line in mamba_input.readlines():
        line = line.rstrip('\n')
        is_blank_line = not line or line.isspace()
        if is_blank_line:
            yield BlankLine(line=line + '\n')
        elif line.startswith('def test_'):
            raise Exception(f"Function needs to be renamed as pytest will think it's a test:\n{line}")
        else:
            indent, tail = _parse_line(line)

            if _MAMBA_IMPORT_PATTERN.match(tail):
                continue

            if _WITH_START_PATTERN.match(tail):
                yield _parse_a_with_line(indent, tail, line)
            else:
                yield LineOfCode(indent=indent, line=line + '\n')


def _parse_line(line: str) -> tuple[int, str]:
    match = _LINE_PATTERN.match(line)
    assert match
    leading_spaces, tail = match.groups()
    assert not tail.startswith('\t')
    indent = len(leading_spaces)
    return indent, tail


def _parse_a_with_line(indent: int, tail: str, line: str) -> WithLine:
    match = _WITH_PATTERN.match(tail)
    assert match, f'Cannot convert this with-line automatically, please simplify it first:\n{line}'
    return WithLine(
        variable=match.group(1).replace('_', '.'),
        name=match.group(2),
        has_as_self=bool(match.group(3)),
        comment=match.group(4),
        line=line + '\n',
        indent=indent,
    )