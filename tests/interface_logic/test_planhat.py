"""
Tests for Planhat interface logic in CRUDs
"""

import pytest

from cruds import Client
from cruds.interface_logic import planhat


@pytest.fixture
def planhat_mock():
    class Interface:
        __init__ = planhat.__init__

    return Interface


def test_Planhat_init(planhat_mock):
    planhat = planhat_mock(company_id="c321", tenant_token="t123")

    assert isinstance(planhat.client, Client)
    assert planhat.company_id == "c321"
    assert planhat.tenant_token == "t123"
