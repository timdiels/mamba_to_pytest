from pathlib import Path

from mamba_to_pytest.main import convert_mamba


def test_convert_foo():
    # You should manually inspect the output
    input_file = Path("test_foo_spec.py")
    output_file = Path("test_foo.py")
    with input_file.open() as mamba_in:
        with output_file.open('w') as pytest_out:
            convert_mamba(mamba_in, pytest_out)