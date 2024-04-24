"""
Tests for Planhat interface logic in CRUDs
"""

import pytest

from cruds import Client
from cruds.interface import Planhat
from cruds.interface_logic.planhat import PlanhatUpsertError


@pytest.fixture
def planhat():
    planhat = Planhat(company_id="c321", tenant_token="t123")
    return planhat


def test_Planhat_init(planhat):
    """
    Check to see if the init holds the company_id, tenant_token and delay
    """

    assert isinstance(planhat.client, Client)
    assert planhat.company_id == "c321"
    assert planhat.tenant_token == "t123"
    assert planhat._delay == 0.3


def test_Planhat_bulk_upsert_response_check_empty(planhat):
    """
    Check to see if the init holds the company_id, tenant_token and delay
    """

    assert planhat.bulk_upsert_response == []
    assert planhat.bulk_upsert_response_check() is None


def test_Planhat_bulk_upsert_response_check_no_errors(planhat):
    """
    Check to see if the init holds the company_id, tenant_token and delay
    """

    planhat.bulk_upsert_response = [
        {
            "created": 0,
            "createdErrors": [],
            "insertsKeys": [],
            "updated": 0,
            "updatedErrors": [],
            "updatesKeys": [],
            "nonupdates": 0,
            "modified": [],
            "upsertedIds": [],
            "permissionErrors": []
        }
    ]
    assert planhat.bulk_upsert_response_check() is None


def test_Planhat_bulk_upsert_response_check_with_errors(planhat):
    """
    Check to see if the init holds the company_id, tenant_token and delay
    """

    planhat.bulk_upsert_response = [
        {
            "created": 0,
            "createdErrors": ["email duplicated"],
            "insertsKeys": [],
            "updated": 0,
            "updatedErrors": ["invalid id"],
            "updatesKeys": [],
            "nonupdates": 0,
            "modified": [],
            "upsertedIds": [],
            "permissionErrors": []
        }
    ]
    with pytest.raises(PlanhatUpsertError) as excinfo:
        planhat.bulk_upsert_response_check()

    assert "Errors found: ['email duplicated']" == str(excinfo.value)
