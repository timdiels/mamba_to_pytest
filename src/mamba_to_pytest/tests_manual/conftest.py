from __future__ import annotations
from copy import copy

import pytest


class MambaVars:
    def copy(self) -> MambaVars:
        return copy(self)


@pytest.fixture(scope="module")
def mamba_cls():
    return MambaVars()


@pytest.fixture
def mamba(mamba_cls):
    return mamba_cls.copy()
