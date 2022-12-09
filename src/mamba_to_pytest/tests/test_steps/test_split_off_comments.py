from __future__ import annotations

from mamba_to_pytest.lines import WithLine, LineOfCode
from mamba_to_pytest.steps.split_off_comments import split_off_comments


def test_split_off_comments():
    line = LineOfCode(indent=0, line='leave me alone\n'),
    lines = [
        WithLine(
            indent=2, line='with var1:\n', variable='it', name='name 1', comment='# comment 1', has_as_self=False
        ),
        line,
    ]

    lines = tuple(split_off_comments(lines))

    assert lines == (
        LineOfCode(indent=2, line="  # comment 1\n"),
        WithLine(indent=2, line='with var1:\n', variable='it', name='name 1', comment=None, has_as_self=False),
        line,
    )
