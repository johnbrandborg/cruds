"""
Tests for Planhat interface logic in CRUDs
"""

from unittest.mock import Mock

import pytest

from cruds import Client
from cruds.interfaces.planhat import Planhat
from cruds.interfaces.planhat.models import *


@pytest.fixture
def planhat():
    planhat = Planhat(company_id="c321", tenant_token="t123")
    return planhat


@pytest.fixture
def planhat_model():
    class Model:
        __init__ = model_init
        create = create
        delete = delete
        get_by_id = get_by_id
        update = update

    return Model(Mock(), "planhat_model_uri")


def test_Planhat_init(planhat):
    """
    Check to see if the init holds the company_id, tenant_token and delay
    """

    assert isinstance(planhat.client, Client)
    assert planhat.company_id == "c321"
    assert planhat.tenant_token == "t123"

    assert planhat._delay == 0.3
    assert planhat.calls_per_min == 200


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


def test_Planhat_model_init(planhat_model):
    """
    The Model Class instances should have the relevant attributes to
    function properly
    """

    assert planhat_model._uri == "planhat_model_uri"
    assert hasattr(planhat_model, "_owner") \
            and isinstance(planhat_model._owner, Mock)


def test_Planhat_create(planhat_model):
    """
    Test the create request to planhat
    """

    create_sample = {"_id": "1"}
    planhat_model.create(data=create_sample)
    planhat_model._owner.client.create.assert_called_with(
        'planhat_model_uri',
        create_sample
    )


def test_Planhat_delete(planhat_model):
    """
    Test the create request to planhat
    """

    native_id = "3248234"
    planhat_model.delete(native_id)

    planhat_model._owner.client.delete.assert_called_with(
        f"planhat_model_uri/{native_id}"
    )


def test_Planhat_update(planhat_model):
    """
    Test the update request to planhat
    """

    native_id = "3248234"
    update_sample = {"name": "John"}
    planhat_model.update(native_id, update_sample)

    planhat_model._owner.client.update.assert_called_with(
        f"planhat_model_uri/{native_id}",
        update_sample
    )



def test_Planhat_get_by_id(planhat_model):
    """
    Test the get_by_id request to planhat
    """

    native_id = "3248234"
    planhat_model.get_by_id(native_id)
    planhat_model._owner.client.read.assert_called_with(
        f"planhat_model_uri/{native_id}",
    )
