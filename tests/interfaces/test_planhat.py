"""
Tests for Planhat interface logic in CRUDs
"""

from collections.abc import Generator
from copy import deepcopy
import json
from re import I
from unittest.mock import MagicMock, Mock

import pytest

from cruds import Client
from cruds.interfaces.planhat import Planhat
from cruds.interfaces.planhat.logic import *
from cruds.interfaces.planhat.logic import _get_all_data


TEST_API_TOKEN = "9PhAfMO3WllHUmmhJA4eO3tJPhDck1aKLvQ5osvNUfKYdJ7H"
TEST_COMPANY_ID = "8IfbCnRP4HGAarzxVop1AS3I"
TEST_TENANT_TOKEN = "1d5df0f5-f217-49da-8997-2878f5986a9f"

EXAMPLE_GET_DIMENSION_DATA = json.loads("""\
[
    {
        "_id": "611ef080ff18a32f886e40ae",
        "dimensionId": "testdim",
        "time": "2021-08-20T00:00:00.000Z",
        "value": 5,
        "model": "Company",
        "parentId": "611547eebcdda93cc7622958",
        "companyId": "611547eebcdda93cc7622958",
        "companyName": "Tenet"
    },
    {
        "_id": "611ef080eb75161dc055880a",
        "dimensionId": "testdim",
        "time": "2021-08-20T00:00:00.000Z",
        "value": 4,
        "model": "Company",
        "parentId": "611547eebcdda93cc7622958",
        "companyId": "611547eebcdda93cc7622958",
        "companyName": "Tenet"
    },
    {
        "_id": "611ef080b067346dfd91ad22",
        "dimensionId": "testdim",
        "time": "2021-08-20T00:00:00.000Z",
        "value": 15,
        "model": "Company",
        "parentId": "611547eebcdda93cc7622958",
        "companyId": "611547eebcdda93cc7622958",
        "companyName": "Tenet"
    }
]
""")

EXAMPLE_GET_LIST_DATA = json.loads("""\
[
    {
        "_id": "60fb0869694ea374023924cb",
        "companyId": "56bccdf554d64d837d01be4a",
        "name": "ZPA Product"
    },
    {
        "_id": "601c0a253e5ed41388982528",
        "companyId": "6011889f52181c5640bf41ba",
        "name": "Trello.io"
    }
]
""")


def api_responses(example_data, number) -> Generator:
    """
    Takes an example payload, and returns chunks like the Planhat API does.
    If the API returns two responses perfectly againsts the limit an extract
    request is made by the Interface with no data returned so it understands
    to stop making requests.
    """
    for i in range(0, len(example_data), number):
        yield example_data[i:i + number]

    yield []


@pytest.fixture
def planhat():
    planhat = Planhat(TEST_API_TOKEN, tenant_token=TEST_TENANT_TOKEN)
    return planhat


@pytest.fixture
def planhat_model():
    class Model:
        __init__ = model_init
        _get_all_data = _get_all_data
        bulk_insert_metrics = bulk_insert_metrics
        bulk_upsert = bulk_upsert
        create = create
        create_activity = create_activity
        delete = delete
        epoc_days_format = epoc_days_format
        get_by_id = get_by_id
        get_dimension_data = get_dimension_data
        get_lean_list = get_lean_list
        get_list = get_list
        update = update
        segment = segment

    model = Model(Mock(), "planhat_model_uri")
    model._owner.bulk_upsert_response = []
    model._owner._delay = 0
    model._owner.tenant_token = TEST_TENANT_TOKEN

    return model


def test_Planhat_init(planhat):
    """
    Check to see if the init holds the company_id, and delay for rate limiting
    """
    EXCEPTED_AUTH_HEADER = "Bearer 9PhAfMO3WllHUmmhJA4eO3tJPhDck1aKLvQ5osvNUfKYdJ7H"

    assert isinstance(planhat.client, Client)
    assert planhat.client._request_headers["Authorization"] == EXCEPTED_AUTH_HEADER

    assert planhat._delay == 0.3
    assert planhat.calls_per_min == 200


def test_Planhat_init_analytics():
    """
    Check to see if the init holds the tenant_token and a client for the analytics
    API
    """

    planhat = Planhat(TEST_API_TOKEN, tenant_token=TEST_TENANT_TOKEN)

    assert planhat.tenant_token == TEST_TENANT_TOKEN
    assert isinstance(planhat.client_analytics, Client)


def test_Planhat_init_analytics_with_no_tenant_token():
    """
    If no tenant token is supplied, trying to retrieve it raises an exception
    """

    planhat = Planhat(TEST_API_TOKEN)

    with pytest.raises(RuntimeError):
        planhat.tenant_token


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


def test_Model_epoc_days_format(planhat_model):
    """
    Check that Epoc days converts datetime strings to the correct int value
    """

    assert planhat_model.epoc_days_format("1975-06-01") == 1977
    assert planhat_model.epoc_days_format("2022-04-15") == 19097


def test_Model_model_init(planhat_model):
    """
    The Model Class instances should have the relevant attributes to
    function properly
    """

    assert planhat_model._uri == "planhat_model_uri"
    assert hasattr(planhat_model, "_owner") \
            and isinstance(planhat_model._owner, Mock)


def test_Model_create(planhat_model):
    """
    Test the create request to planhat
    """

    create_sample = {"_id": "1"}
    planhat_model.create(data=create_sample)

    planhat_model._owner.client.create.assert_called_with(
        'planhat_model_uri',
        create_sample
    )


def test_Model_bulk_upsert_with_patch(planhat_model):
    """
    Test the bulk upsert can use patch
    """
    bulk_upsert_sample = [{"_id": "1"}]

    planhat_model.bulk_upsert(
        bulk_upsert_sample,
        with_post=False,
    )
    planhat_model._owner.client.update.assert_called()


def test_Model_bulk_upsert_with_post(planhat_model):
    """
    Test the bulk upsert can use post
    """
    bulk_upsert_sample = [{"_id": "1"}]

    planhat_model.bulk_upsert(
        bulk_upsert_sample,
        with_post=True,
    )
    planhat_model._owner.client.create.assert_called()


def test_Model_bulk_upsert_results(planhat_model):
    """
    Test the bulk upsert iterates over data and returns results
    """
    bulk_upsert_sample = [
        {"_id": "2"},
        {"_id": "3"},
        {"_id": "1"},
    ]

    def response(self, data):
        return [d.get("_id", "") for d in data]

    planhat_model._owner.client.update = response

    # Run twice to ensure results are cleared each time
    planhat_model.bulk_upsert(bulk_upsert_sample)
    results = planhat_model.bulk_upsert(
        bulk_upsert_sample,
        chunk_size=1,
    )

    expected_results = [["2"], ["3"], ["1"]]

    assert results == expected_results
    assert planhat_model._owner.bulk_upsert_response == expected_results


def test_Model_bulk_upsert_chunksize_two(planhat_model):
    """
    Test the bulk upsert iterates with specific chunk sizes
    """

    bulk_upsert_sample = [
        {"_id": "1"},
        {"_id": "2"},
        {"_id": "3"},
        {"_id": "4"},
        {"_id": "5"},
    ]

    planhat_model.bulk_upsert(
        bulk_upsert_sample,
        chunk_size=3,
    )

    assert planhat_model._owner.client.update.call_count == 2
    planhat_model._owner.client.update.assert_called_with(
        "planhat_model_uri",
        [
            {"_id": "4"},
            {"_id": "5"},
        ]
    )


def test_Model_delete(planhat_model):
    """
    Test the create request to planhat
    """

    native_id = "3248234"
    planhat_model.delete(native_id)

    planhat_model._owner.client.delete.assert_called_with(
        f"planhat_model_uri/{native_id}"
    )


def test_Model_update(planhat_model):
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


def test_Model_get_by_id(planhat_model):
    """
    Test the get_by_id request to planhat
    """

    native_id = "3248234"
    planhat_model.get_by_id(native_id)
    planhat_model._owner.client.read.assert_called_with(
        f"planhat_model_uri/{native_id}",
    )


def test_Model_get_lean_list(planhat_model):
    """
    Test the get_lean_list request to planhat
    """
    planhat_model.get_lean_list()

    planhat_model._owner.client.read.assert_called_with(
        f"leancompanies",
        params={},
    )


def test_Model_get_lean_list_externl_id(planhat_model):
    """
    Test the get_lean_list request to planhat by external id
    """

    planhat_model.get_lean_list(external_id="chevron")

    planhat_model._owner.client.read.assert_called_with(
        f"leancompanies",
        params={"externalId": "chevron"},
    )


def test_Model_get_lean_list_source_id(planhat_model):
    """
    Test the get_lean_list request to planhat by source id
    """
    planhat_model.get_lean_list(source_id="0012000001UchdsAAB")

    planhat_model._owner.client.read.assert_called_with(
        f"leancompanies",
        params={"sourceId": "0012000001UchdsAAB"},
    )


def test_Model_get_lean_list_status_list(planhat_model):
    """
    Test the get_lean_list request to planhat with a status list
    """
    planhat_model.get_lean_list(status=["lost", "prospect"])
    planhat_model._owner.client.read.assert_called_with(
        f"leancompanies",
        params={"status": ["lost", "prospect"]},
    )


def test_Model_get_lean_list_status_string(planhat_model):
    """
    Test the get_lean_list request to planhat with a status string
    """
    planhat_model.get_lean_list(status="lost, prospect")
    planhat_model._owner.client.read.assert_called_with(
        f"leancompanies",
        params={"status": ["lost", "prospect"]},
    )


def test_Model_get_dimension_generator(planhat_model):
    """
    Test the get_dimension_data method creates a generator
    """
    planhat_model._get_all_data = MagicMock()
    planhat_model._get_all_data.return_value = iter(EXAMPLE_GET_DIMENSION_DATA)

    get_dimension_gen: Generator = planhat_model.get_dimension_data(
        from_day=1,
        to_day=1,
    )
    assert isinstance(get_dimension_gen, Generator)

    for index, response in enumerate(get_dimension_gen):
        assert response == EXAMPLE_GET_DIMENSION_DATA[index]

    planhat_model._get_all_data.assert_called_with(
        "planhat_model_uri",
        {
            "from": 1,
            "to": 1,
            "limit": 10000,
            "offset": 0
        },
        0,
    )


def test_Model_get_dimension_generator_with_company_and_dimension(planhat_model):
    """
    Test the get_dimension_data method creates a generator
    """
    planhat_model._get_all_data = MagicMock()
    planhat_model._get_all_data.return_value = iter(EXAMPLE_GET_DIMENSION_DATA)

    planhat_model.get_dimension_data(
        from_day=1,
        to_day=1,
        company_id=100,
        dimension_id="asset",
    ).__next__()

    planhat_model._get_all_data.assert_called_with(
        "planhat_model_uri",
        {
            "from": 1,
            "to": 1,
            "limit": 10000,
            "offset": 0,
            "cId": 100,
            "dimid": "asset",
        },
        0,
    )

def test_Model_get_list_generator(planhat_model):
    """
    Test the get dimension data method creates a sub generator off _get_all_data
    """
    planhat_model._get_all_data = MagicMock()
    planhat_model._get_all_data.return_value = iter(EXAMPLE_GET_LIST_DATA)

    get_list_gen: Generator = planhat_model.get_list()
    assert isinstance(get_list_gen, Generator)

    for index, response in enumerate(get_list_gen):
        assert response == EXAMPLE_GET_LIST_DATA[index]

    planhat_model._get_all_data.assert_called_with(
        "planhat_model_uri",
        {
            "sort": "-_id",
            "select": "name, companyId",
            "limit": 2000,
            "offset": 0
        },
        0,
    )

def test_Model__get_all_data_standard(planhat_model):
    """
    Test the get dimension data makes a request with defaults values, in one
    iteration.
    """
    planhat_model._owner.client.read.return_value = EXAMPLE_GET_DIMENSION_DATA

    uri, params = "get_all_standard_uri", {"limit": 2000, "offset": 0}

    for index, data in enumerate(planhat_model._get_all_data(uri, params, 0)):

        planhat_model._owner.client.read.assert_called_with(uri, params)
        assert data == EXAMPLE_GET_DIMENSION_DATA

    assert index == 0


def test_Model__get_all_data_max_requests(planhat_model):
    """
    Test the get dimension data makes a request with max requests set to 1,
    and a limit of 1 value per request.
    """
    step_size: int = 1
    planhat_model._owner.client.read.side_effect = api_responses(
        EXAMPLE_GET_DIMENSION_DATA, step_size
    )

    uri, params = "get_all_max_requests_uri", {"limit": step_size, "offset": 0}

    for index, data in enumerate(planhat_model._get_all_data(uri, params, 1)):

        planhat_model._owner.client.read.assert_called_with(uri, params)
        assert data == [EXAMPLE_GET_DIMENSION_DATA[index]]

    assert index == 0


def test_Model__get_all_data_with_limit_one(planhat_model):
    """
    Test the get dimension data makes multiple requests, with a limit of 1 value
    per request.

    With 3 entries in the example data 4 requests should be made because the
    drop off from the limit occurs only when the payload returned is empty.
    """
    step_size: int = 1
    planhat_model._owner.client.read.side_effect = api_responses(
        EXAMPLE_GET_DIMENSION_DATA, step_size
    )

    uri, params = "get_all_limit_one_uri", {"limit": step_size, "offset": 0}
    updated_params = deepcopy(params)

    for index, data in enumerate(planhat_model._get_all_data(uri, params, 0)):
        step: int = index * step_size

        planhat_model._owner.client.read.assert_called_with(uri, updated_params)
        assert data == EXAMPLE_GET_DIMENSION_DATA[step:step + step_size]

        updated_params["offset"] += step_size
        print("INDEX", index)

    assert index == 3


def test_Model__get_all_data_with_limit_two(planhat_model):
    """
    Test the get dimension data makes multiple requests, with a limit of 2 value
    per request.

    With 3 entries in the example data 2 requests should be made as the drop off
    of data from the limit on the second request causes the generator stop.
    """
    step_size: int = 2
    planhat_model._owner.client.read.side_effect = api_responses(
        EXAMPLE_GET_DIMENSION_DATA, step_size
    )

    uri, params = "get_all_limit_two_uri", {"limit": step_size, "offset": 0}
    updated_params = deepcopy(params)

    for index, data in enumerate(planhat_model._get_all_data(uri, params, 0)):
        step: int = index * step_size

        planhat_model._owner.client.read.assert_called_with(uri, updated_params)
        assert data == EXAMPLE_GET_DIMENSION_DATA[step:step + step_size]

        updated_params["offset"] += step_size

    assert index == 1


## Analytics Endpoint Tests

def test_Model_bulk_insert_metrics(planhat_model):
    """
    Test the bulk insert metrics request to planhat
    """
    bulk_sample: dict[str, Any] = {
        "name": "Ivars Mucenieks",
        "email": "ivars@planhat.com",
        "cId": "abc123",
        "action": "Logged in",
        "weight": 1,
        "count": 1
    }

    planhat_model._owner.tenant_token = TEST_TENANT_TOKEN
    planhat_model.bulk_insert_metrics(bulk_sample)

    planhat_model._owner.client_analytics.update.assert_called_with(
        f"planhat_model_uri/{TEST_TENANT_TOKEN}",
        bulk_sample,
        with_post=True,
    )


def test_Model_create_activity(planhat_model):
    """
    Test the create activity request to planhat
    """

    create_sample = json.loads("""\
    {
        "email": "ivars@planhat.com",
        "action": "Logged in",
        "externalId": "ojpsoi57pzn",
        "companyExternalId": "Planhat-81ock9l81wl",
        "weight": 1,
        "info": {
            "index": 20,
            "theme": "Blue"
        }
    }
    """)
    planhat_model.create_activity(data=create_sample)

    planhat_model._owner.client_analytics.create.assert_called_with(
        f"planhat_model_uri/{TEST_TENANT_TOKEN}",
        create_sample
    )


def test_Model_segment(planhat_model):
    """
    Test the segment request to planhat
    """

    create_sample = json.loads("""\
    {
        "type": "identify",
        "traits": {
            "name": "Ivars Mucenieks",
            "email": "ivars@planhat.com",
            "companyId": "ABCDE"
        }
    }
    """)
    planhat_model.segment(data=create_sample)

    planhat_model._owner.client_analytics.create.assert_called_with(
        "dock/segment",
        create_sample
    )
