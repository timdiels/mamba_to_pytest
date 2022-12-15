from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class CodelessLine:
    """
    A line which has no actual code, e.g. a blank line or a full-line comment
    """
    line: str


@dataclasses.dataclass(frozen=True)
class LineOfCode:
    indent: int

    line: str
    """Original line, including trailing newline"""

    def to_line_of_code(self) -> LineOfCode:
        return LineOfCode(indent=self.indent, line=self.line)


@dataclasses.dataclass(frozen=True)
class WithLine(LineOfCode):
    """
    Represents: with {variable}('{}'): {comment}
    """

    variable: str
    name: str | None

    comment: str | None
    """Trailing comment, starting from the '#'"""


@dataclasses.dataclass(frozen=True)
class ClassHeading(LineOfCode):
    """
    E.g. class Foo:
    """


@dataclasses.dataclass(frozen=True)
class MethodHeading(LineOfCode):
    """
    E.g. def foo(self, x):

    Not necessarily an actual method of a class, just any function with self as first param. It might even be the
    first line of a multiline heading: e.g. def foo(self
    """

    name: str
