import re
from enum import Enum


_TRAILING_COMMENT = r'''\s*(#.*)?'''


LINE_PATTERN = re.compile(r'^( *)([^ ].*)?$')
MAMBA_IMPORT_PATTERN = re.compile(r'''^(from|import) mamba(\s|$)''')


_WITH_START = r'''^with\s+(description|context|describe|it|(?:before|after)[._](?:each|all))\s*'''
WITH_START_PATTERN = re.compile(_WITH_START)
WITH_PATTERN = re.compile(_WITH_START + rf'''(?:[(]['"](.*)['"][)])?( as self)?:{_TRAILING_COMMENT}$''')


CLASS_PATTERN = re.compile(r'''^class\s''')


METHOD_START_PATTERN = re.compile(r'''^def\s+\w+\s*\(\s*self(\W|$)''')
METHOD_PATTERN = re.compile(rf'^def\s+(\w+)\s*\(\s*self[^,]*(?:,\s*([^#]+))?\)([^:#]*:{_TRAILING_COMMENT})$')


class TestScope(Enum):
    METHOD = 'METHOD'
    CLASS = 'CLASS'
