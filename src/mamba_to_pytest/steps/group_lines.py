from __future__ import annotations
import typing as t

from mamba_to_pytest.lines import LineOfCode, WithLine, BlankLine
from mamba_to_pytest.nodes import BlockOfCode


def group_plain_lines(lines: t.Iterable[LineOfCode | BlankLine]) -> t.Iterable[BlockOfCode | WithLine]:
    yield from _LineGrouper()(lines)


class _LineGrouper:
    def __init__(self):
        self._body_lines: list[LineOfCode | BlankLine] = []

    def __call__(self, lines: t.Iterable[LineOfCode | BlankLine]) -> t.Iterable[BlockOfCode | WithLine]:
        for line in lines:
            if isinstance(line, WithLine):
                yield from self._finish_block_if_any()
                yield line
            else:
                if self._has_block and not self._is_line_in_current_block(line):
                    yield from self._finish_block_if_any()
                self._body_lines.append(line)
        yield from self._finish_block_if_any()

    @property
    def _has_block(self):
        return bool(self._body_lines)

    @property
    def _body_indent(self) -> int | None:
        assert self._body_lines
        for line in self._body_lines:
            if not isinstance(line, BlankLine):
                return line.indent
        return None

    def _is_line_in_current_block(self, line: LineOfCode | BlankLine):
        if isinstance(line, BlankLine):
            return True
        body_indent = self._body_indent
        if body_indent is None:
            return True
        return line.indent >= body_indent

    def _finish_block_if_any(self) -> t.Iterable[BlockOfCode]:
        if not self._has_block:
            return

        body = ''.join(line.line for line in self._body_lines)
        indent = self._body_indent
        if indent is None:
            indent = 999999  # a block of blank lines, this hack is hopefully sufficient for the next steps to work
        block = BlockOfCode(indent=indent, body=body)
        self._body_lines = []
        yield block
