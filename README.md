Converts mamba tests to pytest. Usually some manual fixes are required, but it's a good starting point. To verify things went well: compare the number of tests ran, make sure they pass, compare test coverage.

This project is made available under the MIT license.

Install with:

    pip install -r requirements.txt
    pip install -e .

Run with:

    mamba_to_pytest test_1_spec.py test_spec.py ...

The original file is renamed to `disabled_*_disabled.py` so it's no longer picked up by your test runner. You can still
make changes to the disabled file and convert it again if necessary.

Converting entire directories:

    find directory1 directory2 ... -name 'test_*_spec.py' -exec mamba_to_pytest '{}' \+ 
    find directory1 directory2 ... -name 'disabled_*_disabled.py' -exec mamba_to_pytest '{}' \+ 

If the command lists failures, you'll have to make adjustments to the mamba file and rerun it (or contribute a PR to
adjust it automatically). If the tests fail, you can adjust either the mamba file or fix it in the pytest file.

Manual fixes after conversion:

- Prefix test directories with `test_`
- Create a `conftest.py` (see below) at the root of any tests which use the mamba pytest fixture
- ...

The conftest:

```python
from __future__ import annotations
from copy import copy

import pytest


class MambaVars:
    def copy(self) -> MambaVars:
        return copy(self)


@pytest.fixture(scope="class")
def mamba_cls():
    return MambaVars()


@pytest.fixture
def mamba(mamba_cls):
    return mamba_cls.copy()
```