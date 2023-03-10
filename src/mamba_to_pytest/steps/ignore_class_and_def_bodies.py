from __future__ import annotations

import typing as t

from mamba_to_pytest.lines import LineOfCode, CodelessLine, ClassHeading, MethodHeading


def ignore_class_and_def_bodies(lines: t.Iterable[LineOfCode | CodelessLine]) -> t.Iterable[LineOfCode | CodelessLine]:
    active_scope: LineOfCode | None = None
    for line in lines:
        if isinstance(line, CodelessLine):
            yield line
        elif active_scope and line.indent > active_scope.indent:
            yield line.to_line_of_code()
        else:
            active_scope = None
            if isinstance(line, ClassHeading) or isinstance(line, MethodHeading):
                if isinstance(line, ClassHeading):
                    line = line.to_line_of_code()
                active_scope = line
            yield line
