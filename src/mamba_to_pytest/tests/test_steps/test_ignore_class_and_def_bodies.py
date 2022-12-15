from mamba_to_pytest.lines import LineOfCode, WithLine, CodelessLine, ClassHeading, MethodHeading
from mamba_to_pytest.steps.ignore_class_and_def_bodies import ignore_class_and_def_bodies


def _create_with_line(indent: int) -> WithLine:
    return WithLine(indent=indent, line='with line\n', variable='context', name=None, comment=None)


def test_ignore_class_and_def_bodies():
    lines = (
        # Leave lines outside of scope alone
        LineOfCode(indent=0, line='leave me alone\n'),
        CodelessLine(line=' \n'),
        _create_with_line(indent=1),

        # Transform lines other than blanks inside scope to plain lines of code
        ClassHeading(indent=2, line='  start of scope\n'),
        LineOfCode(indent=3, line='leave me alone\n'),
        CodelessLine(line=' \n'),
        _create_with_line(indent=3),

        # Same level (or higher) ends the scope. I.e. these lines remain untouched
        _create_with_line(indent=2),
        _create_with_line(indent=2),

        # Method also starts a scope, but does not itself get transformed
        MethodHeading(indent=1, line='  start of scope\n', name='outer'),
        # Inner scopes get transformed, even methods
        ClassHeading(indent=4, line='  start of scope\n'),
        MethodHeading(indent=4, line='  start of scope\n', name='inner'),
        # and lines outside the inner scope still get transformed
        _create_with_line(indent=3),

        # Does not get confused when a scope appears right after another
        ClassHeading(indent=1, line='  start of scope\n'),
        _create_with_line(indent=3),
        _create_with_line(indent=1),
        _create_with_line(indent=0),
    )

    actual = tuple(ignore_class_and_def_bodies(lines))

    assert actual == (
        # Leave lines outside of scope alone
        LineOfCode(indent=0, line='leave me alone\n'),
        CodelessLine(line=' \n'),
        _create_with_line(indent=1),

        # Transform lines other than blanks inside scope to plain lines of code
        LineOfCode(indent=2, line='  start of scope\n'),
        LineOfCode(indent=3, line='leave me alone\n'),
        CodelessLine(line=' \n'),
        LineOfCode(indent=3, line='with line\n'),

        # Same level (or higher) ends the scope. I.e. these lines remain untouched
        _create_with_line(indent=2),
        _create_with_line(indent=2),

        # Method also starts a scope, but does not itself get transformed
        MethodHeading(indent=1, line='  start of scope\n', name='outer'),
        # Inner scopes get transformed, even methods
        LineOfCode(indent=4, line='  start of scope\n'),
        LineOfCode(indent=4, line='  start of scope\n'),
        # and lines outside the inner scope still get transformed
        LineOfCode(indent=3, line='with line\n'),

        # Does not get confused when a scope appears right after another
        LineOfCode(indent=1, line='  start of scope\n'),
        LineOfCode(indent=3, line='with line\n'),
        _create_with_line(indent=1),
        _create_with_line(indent=0),
    )
