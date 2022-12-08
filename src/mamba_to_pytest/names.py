import re

import inflection


_SPECIAL_CHARS_PATTERN = re.compile(r'[^A-Za-z0-9]+')


def convert_mamba_name_to_class_name(mamba_name: str) -> str:
    parts = _SPECIAL_CHARS_PATTERN.split(mamba_name)
    name = ''.join(inflection.camelize(part) for part in parts)
    return 'Test' + name


def convert_mamba_name_to_method_name(mamba_name: str) -> str:
    parts = _SPECIAL_CHARS_PATTERN.split(mamba_name)
    name = '_'.join(inflection.underscore(part) for part in parts)
    return "test_" + name.rstrip('_')


def prepend_pytest_class_name_to_test_method(cls_name: str, method_name: str) -> str:
    assert cls_name.startswith('Test')
    assert method_name.startswith('test_')
    return f"{inflection.underscore(cls_name)}_{method_name[len('test_'):]}"
