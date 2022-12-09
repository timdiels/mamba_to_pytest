from __future__ import annotations

import dataclasses
import typing as t

from mamba_to_pytest.lines import LineOfCode, WithLine, BlankLine


def split_off_comments(lines: t.Iterable[LineOfCode | BlankLine]) -> t.Iterable[LineOfCode | BlankLine]:
    for line in lines:
        if isinstance(line, WithLine) and line.comment:
            yield LineOfCode(indent=line.indent, line=' ' * line.indent + line.comment + '\n')
            yield dataclasses.replace(line, comment=None)
        else:
            yield line
