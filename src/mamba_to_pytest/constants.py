import re
from enum import Enum


_TRAILING_COMMENT = r'''\s*(#.*)?'''


LINE_PATTERN = re.compile(r'^( *)([^ ].*)?$')
MAMBA_IMPORT_PATTERN = re.compile(r'''^(from|import) mamba(\s|$)''')


_WITH_START = r'''^with\s+(description|context|describe|it|(?:before|after)[._](?:each|all))\s*'''
WITH_START_PATTERN = re.compile(_WITH_START)
WITH_PATTERN = re.compile(_WITH_START + rf'''(?:[(]['"](.*)['"][)])?( as self)?:{_TRAILING_COMMENT}$''')


CLASS_PATTERN = re.compile(r'''^class\s''')


_METHOD_START = r'''^def\s+\w+\(\s*self(\W|$)'''
METHOD_START_PATTERN = re.compile(_METHOD_START)


class TestScope(Enum):
    METHOD = 'METHOD'
    CLASS = 'CLASS'
