from mamba_to_pytest.lines import WithLine, LineOfCode
from mamba_to_pytest.nodes import BlockOfCode
from mamba_to_pytest.steps.group_lines import group_plain_lines


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

        grouped_lines = list(group_plain_lines(lines))

        assert grouped_lines == [
            BlockOfCode(indent=2, body='  line1\n    line2\n        line3\n    line4\n  line5\n'),
            BlockOfCode(indent=1, body=' line6\n'),
        ]

    def test_do_not_group_across_with_lines(self):
        with_line = WithLine(indent=0, line='line3\n', variable='it', name=None, comment=None, has_as_self=False)
        lines = [
            LineOfCode(indent=0, line='line1\n'),
            with_line,
            LineOfCode(indent=0, line='line3\n'),
        ]

        grouped_lines = list(group_plain_lines(lines))

        assert grouped_lines == [
            BlockOfCode(indent=0, body='line1\n'),
            with_line,
            BlockOfCode(indent=0, body='line3\n'),
        ]
