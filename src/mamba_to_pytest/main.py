import re
import sys
import traceback
import typing as t
from pathlib import Path
from textwrap import indent

from mamba_to_pytest.node_visitors.combine_setup_teardown import combine_setup_teardown
from mamba_to_pytest.node_visitors.convert_self_vars import convert_self_vars
from mamba_to_pytest.node_visitors.flatten_singleton_test_contexts import flatten_singleton_test_contexts
from mamba_to_pytest.node_visitors.validate import validate_node
from mamba_to_pytest.node_visitors.write import write_tree
from mamba_to_pytest.steps.group_lines import group_plain_lines
from mamba_to_pytest.steps.convert_with_lines import convert_with_lines, \
    split_off_comments
from mamba_to_pytest.steps.split_mamba import split_mamba


ENABLED_TEST_PATTERN = re.compile(r'test_(.*)_spec.py')
DISABLED_TEST_PATTERN = re.compile(r'disabled_(.*)_disabled.py')


def main():
    convert_mamba_files((Path(path) for path in sys.argv[1:]), raise_if_failed=False)


def convert_mamba_files(files: t.Iterable[Path], raise_if_failed: bool) -> None:
    total = 0
    succeeded = 0
    for mamba_file in files:
        print(f'Convert {mamba_file}')
        total += 1
        try:
            match = DISABLED_TEST_PATTERN.fullmatch(mamba_file.name)
            if match:
                convert_disabled_mamba_file(mamba_file, match)
            else:
                convert_enabled_mamba_file(mamba_file)
            succeeded += 1
        except Exception as exc:
            print(f'{mamba_file} failed')

            if exc.args:
                error = indent(str(exc), '    ')
            else:
                error = traceback.format_exc()
                error = error.splitlines()[-2]

            print(error)
            if raise_if_failed:
                raise
    print(f'{succeeded}/{total} succeeded')


def convert_enabled_mamba_file(mamba_file: Path) -> None:
    if mamba_file.name == 'test_spec.py':
        base_name = 'it'
    else:
        match = ENABLED_TEST_PATTERN.fullmatch(mamba_file.name)
        assert match, f'Does not look like a mamba test file: {mamba_file}'
        base_name = match.group(1)

    out_file = mamba_file.with_name(f'test_{base_name}.py')
    assert not out_file.exists(), f'Output file already exists: {out_file}'
    convert_mamba_file(mamba_file, out_file)

    # Make sure the mamba file no longer runs, while still allowing us to easily convert it again later in case
    # something went wrong
    disabled_file = mamba_file.with_name(f'disabled_{base_name}_disabled.py')
    print(f"    and renaming the original file so it no longer runs\n     to {disabled_file}")
    mamba_file.rename(disabled_file)


def convert_disabled_mamba_file(mamba_file: Path, match: re.Match) -> None:
    base_name = match.group(1)
    out_name = f'test_{base_name}.py'
    out_file = mamba_file.with_name(out_name)
    convert_mamba_file(mamba_file, out_file)


def convert_mamba_file(mamba_file: Path, out_file: Path) -> None:
    print(f'     to {out_file}')
    with mamba_file.open() as mamba_input:
        try:
            with out_file.open('w') as out:
                convert_mamba(mamba_input, out)
        except Exception:
            out_file.unlink()
            raise


def convert_mamba(mamba_input: t.TextIO, pytest_output: t.TextIO):
    lines = split_mamba(mamba_input)
    lines = split_off_comments(lines)
    blocks_and_lines = group_plain_lines(lines)
    root = convert_with_lines(blocks_and_lines)
    root = flatten_singleton_test_contexts(root)
    root = combine_setup_teardown(root)
    validate_node(root)
    root = convert_self_vars(root)
    write_tree(root, pytest_output)


if __name__ == '__main__':
    main()
