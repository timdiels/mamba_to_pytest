import re
from enum import Enum


_TRAILING_COMMENT = r'''\s*(#.*)?'''


LINE_PATTERN = re.compile(r'^( *)([^ ].*)?$')
MAMBA_IMPORT_PATTERN = re.compile(r'''^(from|import) mamba(\s|$)''')


_WITH_START = r'''^with\s+(description|context|describe|it|(?:before|after)[._](?:each|all))\s*'''
WITH_START_PATTERN = re.compile(_WITH_START)
WITH_PATTERN = re.compile(_WITH_START + rf'''(?:[(]['"](.*)['"][)])?(?: as self)?:{_TRAILING_COMMENT}$''')


CLASS_PATTERN = re.compile(r'''^class\s''')


METHOD_START_PATTERN = re.compile(r'''^def\s+(\w+)\s*\(\s*self(?:\W|$)''')


class TestScope(Enum):
    METHOD = 'METHOD', 'mamba'
    CLASS = 'CLASS', 'mamba_cls'

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, value, fixture_name):
        self._value_ = value
        self._fixture_name = fixture_name

    @property
    def fixture_name(self) -> str:
        return self._fixture_name
