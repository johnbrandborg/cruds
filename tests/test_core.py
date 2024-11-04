"""
Tests for Core components in CRUDs
"""

from unittest import mock

import pytest
import urllib3

import cruds
from cruds.core import AuthABC

request_headers = urllib3.HTTPHeaderDict()


def test_Client_token_authentication():
    """
    Supplying an 'auth' string will placed into the header for bearer token
    authenticationi.
    """
    api = cruds.Client(host="https://localhost", auth="api_token")
    assert api.request_headers.get("Authorization") == "Bearer api_token"


def test_Client_basic_authentication():
    """
    Supplying an 'auth' tuple or list will placed into the header for basic
    authentication.
    """
    api = cruds.Client(host="https://localhost", auth=("username", "password"))
    assert api.request_headers.get("authorization") == "Basic dXNlcm5hbWU6cGFzc3dvcmQ="


def test_Client_creates_urllib3_manager():
    """
    When no URLLib3 manager is suppied, a manager is automatically created.
    """
    api = cruds.Client(host="https://localhost")
    assert isinstance(api.manager, urllib3.PoolManager)


def test_Client_use_supplied_urllib3_manager():
    """
    When a URLLib3 manager is suppied use it, instead of creating one.
    """
    api = cruds.Client(host="https://localhost", manager=urllib3.PoolManager())
    assert isinstance(api.manager, urllib3.PoolManager)


def test_Client_disable_retries():
    """Setting the retries to 0 or None will disable retries being used"""
    api = cruds.Client(host="https://localhost", retries=0)
    assert api.manager.connection_pool_kw.get("retries") == 0

    cruds.Client(host="https://localhost", retries=None)
    assert api.manager.connection_pool_kw.get("retries") == 0


@pytest.fixture
def crud_api():
    """
    Creates a Client Client without response processing.
    """
    api = cruds.Client(host="https://localhost", retries=0)
    mock_resp = urllib3.HTTPResponse(body=b'{"name": "test"}')
    api.manager.request = mock.Mock(return_value=mock_resp)
    api._process_resp = lambda method, resp: resp
    return api


def test_Client_create_operation(crud_api):
    """Check the Create Operation formats the request properly"""
    sample = {"test_name": "test_Client_create_operation"}
    resp = crud_api.create("user/1", data=sample)

    crud_api.manager.request.assert_called_with(
        "POST",
        "https://localhost/user/1",
        headers=request_headers,
        json=sample,
    )
    assert resp.data == b'{"name": "test"}'


def test_Client_create_operation_with_bytes(crud_api):
    """
    Check the Create Operation formats the request properly.
    """
    sample = b'{"test_name": "test_Client_create_operation"}'
    resp = crud_api.create("user/2", data=sample)

    crud_api.manager.request.assert_called_with(
        "POST",
        "https://localhost/user/2",
        json=sample,
        headers=request_headers,
    )
    assert resp.data == b'{"name": "test"}'

    crud_api.serialize = False
    resp = crud_api.create("user/2", data=sample)
    crud_api.manager.request.assert_called_with(
        "POST",
        "https://localhost/user/2",
        body=sample,
        headers=request_headers,
    )
    assert resp.data == b'{"name": "test"}'


def test_Client_read_operation(crud_api):
    """
    Check the Read Operation formats the request properly.
    """
    resp = crud_api.read("test")

    crud_api.manager.request.assert_called_with(
        "GET",
        "https://localhost/test",
        fields=None,
        headers=request_headers,
    )
    assert resp.data == b'{"name": "test"}'


def test_Client_update_operation(crud_api):
    """
    Check the Update Operation formats the request properly.
    """
    sample = {"test_name": "test_Client_update_operation"}
    resp = crud_api.update("test", data=sample)

    crud_api.manager.request.assert_called_with(
        "PATCH",
        "https://localhost/test",
        headers=request_headers,
        json=sample,
    )
    assert resp.data == b'{"name": "test"}'


def test_Client_update_operation_with_bytes(crud_api):
    """
    Check the Update Operation formats the request properly.
    """
    sample = b'{"test_name": "test_Client_update_operation"}'
    resp = crud_api.update("test", data=sample)

    crud_api.manager.request.assert_called_with(
        "PATCH",
        "https://localhost/test",
        json=sample,
        headers=request_headers,
    )
    assert resp.data == b'{"name": "test"}'

    crud_api.serialize = False
    resp = crud_api.update("test", data=sample)
    crud_api.manager.request.assert_called_with(
        "PATCH",
        "https://localhost/test",
        body=sample,
        headers=request_headers,
    )
    assert resp.data == b'{"name": "test"}'


def test_Client_update_operation_with_replace(crud_api):
    """
    Check the Update Operation formats the request properly.
    """
    sample = {"test_name": "test_Client_update_operation"}
    resp = crud_api.update("test", data=sample, replace=True)

    crud_api.manager.request.assert_called_with(
        "PUT",
        "https://localhost/test",
        headers=request_headers,
        json=sample,
    )
    assert resp.data == b'{"name": "test"}'


def test_Client_delete_operation(crud_api):
    """
    Check the Delete Operation formats the request properly.
    """
    resp = crud_api.delete("test")

    crud_api.manager.request.assert_called_with(
        "DELETE",
        "https://localhost/test",
        fields=None,
        headers=request_headers,
    )
    assert resp.data == b'{"name": "test"}'


def test_Client_process_resp_return_bytes():
    """
    Check the response processing returns bytes for non-JSON content.
    """
    api = cruds.Client(host="https://localhost")
    mock_resp = urllib3.HTTPResponse(
        body=b"name=test_Client_process_resp_return_bytes", status=399
    )
    assert (
        api._process_resp("", mock_resp)
        == b"name=test_Client_process_resp_return_bytes"
    )


def test_Client_process_resp_return_bytes_with_serialize_false():
    """
    Check the response processing returns bytes for JSON content when serialize
    is disabled.
    """
    api = cruds.Client(host="https://localhost", serialize=False)
    mock_resp = urllib3.HTTPResponse(
        body=b'{"name": "test_Client_process_resp_return_bytes_with_serialize_false"}',
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    assert (
        api._process_resp("", mock_resp)
        == b'{"name": "test_Client_process_resp_return_bytes_with_serialize_false"}'
    )


def test_Client_process_resp_return_dictionary():
    """
    Check the response processing returns a dictionary for JSON content.
    """
    api = cruds.Client(host="https://localhost")
    mock_resp = urllib3.HTTPResponse(
        body=b'{"name": "test_Client_process_resp_return_dictionary"}',
        headers={"Content-Type": "application/json; charset=utf-8"},
        status=399,
    )
    assert api._process_resp("", mock_resp) == {
        "name": "test_Client_process_resp_return_dictionary"
    }


def test_Client_raise_status_399():
    """
    Check the response return code of 399 doesn't raise an exceptions.
    """
    api = cruds.Client(host="https://localhost")
    mock_resp = urllib3.HTTPResponse(body=b'{"name": "test"}', status=399)
    api._process_resp("", mock_resp)


def test_Client_raise_status_400():
    """
    Check the response status code 400 raises an exception.
    """
    api = cruds.Client(host="https://localhost")
    mock_resp = urllib3.HTTPResponse(body=b'{"name": "test"}', status=400)
    with pytest.raises(urllib3.exceptions.HTTPError):
        api._process_resp("", mock_resp)


def test_Client_raise_status_500():
    """
    Check the response status code 500 raises an exception.
    """
    api = cruds.Client(host="https://localhost")
    mock_resp = urllib3.HTTPResponse(body=b'{"name": "test"}', status=500)
    with pytest.raises(urllib3.exceptions.HTTPError):
        api._process_resp("", mock_resp)


def test_Client_raise_status_ignore():
    """
    Check the response status code 400 doesn't raises an exception when ignored.
    """
    api = cruds.Client(host="https://localhost", retries=0)
    api.status_ignore.add(400)
    mock_resp = urllib3.HTTPResponse(body=b'{"name": "test"}', status=400)
    api._process_resp("", mock_resp)


def test__check_auth_invalid():
    """
    If the auth attribute is found and token is invalid retrieve new token to
    the request headers.
    """

    class MockAuth(AuthABC):
        def access_token(self):
            return "9a8sdftg"

        def is_valid(self):
            return False

    api = cruds.Client(host="https://localhost", auth=MockAuth())
    assert api.request_headers.get("Authorization") == "Bearer 9a8sdftg"


def test__check_auth_still_valid():
    """
    If the auth attribute is found and token is valid do nothing to the request
    headers.
    """

    class MockAuth(AuthABC):
        def access_token(self):
            return "9a8sdftg"  # TODO Mock this to test side effects rather than None.

        def is_valid(self):
            return True

    api = cruds.Client(host="https://localhost", auth=MockAuth())
    assert api.request_headers.get("Authorization") is None
