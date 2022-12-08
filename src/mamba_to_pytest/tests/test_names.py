import pytest

from mamba_to_pytest.names import convert_mamba_name_to_method_name, convert_mamba_name_to_class_name


@pytest.mark.parametrize(
    'name, expected',
    (
        ('simple thing1 2', 'TestSimpleThing12'),
        ('snake_case space', 'TestSnakeCaseSpace'),
        ("Replace weird characters ~!@#$%^^&**()_+{}[]:<>?|,./\"\\'like this", 'TestReplaceWeirdCharactersLikeThis')
    ),
)
def test_to_class_name(name, expected):
    assert convert_mamba_name_to_class_name(name) == expected


@pytest.mark.parametrize(
    'name, expected',
    (
        ('simple thing1 2', 'test_simple_thing1_2'),
        ('CamelCase Space', 'test_camel_case_space'),
        (r'''Replace weird characters ~!@#$%^^&**()_+{}[]:<>?|,./\"'like this''', 'test_replace_weird_characters_like_this')
    ),
)
def test_to_method_name(name, expected):
    assert convert_mamba_name_to_method_name(name) == expected
