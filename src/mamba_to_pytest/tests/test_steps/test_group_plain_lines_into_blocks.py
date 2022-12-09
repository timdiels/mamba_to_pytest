import pytest

from mamba_to_pytest.lines import WithLine, LineOfCode, MethodHeading
from mamba_to_pytest.nodes import BlockOfCode
from mamba_to_pytest.steps.group_plain_lines_into_blocks import group_plain_lines_into_blocks


class TestGroupPlainLines:
    def test_group_lines_at_current_indent_or_lower(self):
        with_line = WithLine(indent=0, line='line3\n', variable='it', name=None, comment=None, has_as_self=False),
        lines = [
            LineOfCode(indent=2, line='  line1\n'),
            LineOfCode(indent=4, line='    line2\n'),
            LineOfCode(indent=8, line='        line3\n'),
            LineOfCode(indent=4, line='    line4\n'),
            LineOfCode(indent=2, line='  line5\n'),
            LineOfCode(indent=1, line=' line6\n'),
        ]

        grouped_lines = list(group_plain_lines_into_blocks(lines))

        assert grouped_lines == [
            BlockOfCode(indent=2, body='  line1\n    line2\n        line3\n    line4\n  line5\n'),
            BlockOfCode(indent=1, body=' line6\n'),
        ]

    @pytest.mark.parametrize(
        'separator_line',
        (
            WithLine(indent=0, line='line3\n', variable='it', name=None, comment=None, has_as_self=False),
            MethodHeading(indent=0, line='line3\n', tail='line3\n'),
        ),
    )
    def test_do_not_group_across_separator_lines(self, separator_line):
        lines = [
            LineOfCode(indent=0, line='line1\n'),
            separator_line,
            LineOfCode(indent=0, line='line3\n'),
        ]

        grouped_lines = list(group_plain_lines_into_blocks(lines))

        assert grouped_lines == [
            BlockOfCode(indent=0, body='line1\n'),
            separator_line,
            BlockOfCode(indent=0, body='line3\n'),
        ]
