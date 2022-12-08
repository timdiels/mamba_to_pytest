from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class BlankLine:
    line: str


@dataclasses.dataclass(frozen=True)
class LineOfCode:
    indent: int
    line: str


@dataclasses.dataclass(frozen=True)
class WithLine(LineOfCode):
    """
    Represents: with {variable}('{}'): {comment}
    """

    variable: str
    name: str | None
    has_as_self: bool

    comment: str | None
    """Trailing comment, starting from the '#'"""

