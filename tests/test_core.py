"""
Pytests for Platforms in RESTful Platform2
"""

from unittest import mock
import pytest
import urllib3

import cruds
from cruds.core import DEFAULT_TIMEOUT


def test_Platform_token_authentication():
    """
    Supplying an 'auth' string will placed into the header for bearer token
    authenticationi.
    """
    api = cruds.Client(host="https://localhost", auth="api_token")
    assert api._http.headers.get("Authorization") == "Bearer api_token"


def test_Platform_basic_authentication():
    """
    Supplying an 'auth' tuple or list will placed into the header for basic
    authentication.
    """
    api = cruds.Client(host="https://localhost", auth=("username", "password"))
    assert api._http.headers.get("authorization") == "Basic dXNlcm5hbWU6cGFzc3dvcmQ="


def test_Platform_creates_urllib3_manager():
    """
    When no URLLib3 manager is suppied, a manager is automatically created.
    """
    api = cruds.Client(host="https://localhost")
    assert isinstance(api._http, urllib3.PoolManager)


def test_Platform_use_supplied_urllib3_manager():
    """
    When a URLLib3 manager is suppied use it, instead of creating one.
    """
    api = cruds.Client(host="https://localhost", manager=urllib3.PoolManager())
    assert isinstance(api._http, urllib3.PoolManager)


def test_Platform_disable_retries():
    """ Setting the retries to 0 or None will disable retries being used """
    api = cruds.Client(host="https://localhost", retries=0)
    assert api._http.connection_pool_kw.get("retries") == 0

    cruds.Client(host="https://localhost", retries=None)
    assert api._http.connection_pool_kw.get("retries") == 0


@pytest.fixture
def crud_api():
    """
    Creates a Platform Platform without response processing.
    """
    api = cruds.Client(host="https://localhost", retries=0)
    mock_resp = urllib3.HTTPResponse(body=b'{"name": "test"}')
    api._http.request = mock.Mock(return_value=mock_resp)
    api._process_resp = lambda method, resp: resp
    return api


def test_Platform_create_operation(crud_api):
    """ Check the Create Operation formats the request properly """
    sample = {"test_name": "test_Platform_create_operation"}
    resp = crud_api.create("user/1", data=sample)

    crud_api._http.request.assert_called_with("POST",
                                              "https://localhost/user/1",
                                              json=sample,
                                              timeout=DEFAULT_TIMEOUT)
    assert resp.data == b'{"name": "test"}'


def test_Platform_create_operation_with_bytes(crud_api):
    """
    Check the Create Operation formats the request properly.
    """
    sample = b'{"test_name": "test_Platform_create_operation"}'
    resp = crud_api.create("user/2", data=sample)

    crud_api._http.request.assert_called_with("POST",
                                              "https://localhost/user/2",
                                              body=sample,
                                              timeout=DEFAULT_TIMEOUT)
    assert resp.data == b'{"name": "test"}'


def test_Platform_read_operation(crud_api):
    """
    Check the Read Operation formats the request properly.
    """
    resp = crud_api.read("test")

    crud_api._http.request.assert_called_with("GET",
                                              "https://localhost/test",
                                              fields=None,
                                              timeout=DEFAULT_TIMEOUT)
    assert resp.data == b'{"name": "test"}'


def test_Platform_update_operation(crud_api):
    """
    Check the Update Operation formats the request properly.
    """
    sample = {"test_name": "test_Platform_update_operation"}
    resp = crud_api.update("test", data=sample)

    crud_api._http.request.assert_called_with("PATCH",
                                              "https://localhost/test",
                                              json=sample,
                                              timeout=DEFAULT_TIMEOUT)
    assert resp.data == b'{"name": "test"}'


def test_Platform_update_operation_with_bytes(crud_api):
    """
    Check the Update Operation formats the request properly.
    """
    sample = b'{"test_name": "test_Platform_update_operation"}'
    resp = crud_api.update("test", data=sample)

    crud_api._http.request.assert_called_with("PATCH",
                                              "https://localhost/test",
                                              body=sample,
                                              timeout=DEFAULT_TIMEOUT)
    assert resp.data == b'{"name": "test"}'


def test_Platform_update_operation_with_replace(crud_api):
    """
    Check the Update Operation formats the request properly.
    """
    sample = {"test_name": "test_Platform_update_operation"}
    resp = crud_api.update("test", data=sample, replace=True)

    crud_api._http.request.assert_called_with("PUT",
                                              "https://localhost/test",
                                              json=sample,
                                              timeout=DEFAULT_TIMEOUT)
    assert resp.data == b'{"name": "test"}'


def test_Platform_delete_operation(crud_api):
    """
    Check the Delete Operation formats the request properly.
    """
    resp = crud_api.delete("test")

    crud_api._http.request.assert_called_with("DELETE",
                                              "https://localhost/test",
                                              fields=None,
                                              timeout=DEFAULT_TIMEOUT)
    assert resp.data == b'{"name": "test"}'


def test_Platform_process_resp_return_bytes():
    """
    Check the response processing returns bytes for non-JSON content.
    """
    api = cruds.Client(host="https://localhost")
    mock_resp = urllib3.HTTPResponse(body=b"name=test_Platform_process_resp_return_bytes", status=399)
    assert api._process_resp("", mock_resp) == b"name=test_Platform_process_resp_return_bytes"


def test_Platform_process_resp_return_bytes_with_serialize_false():
    """
    Check the response processing returns bytes for JSON content when serialize
    is disabled.
    """
    api = cruds.Client(host="https://localhost", serialize=False)
    mock_resp = urllib3.HTTPResponse(
            body=b'{"name": "test_Platform_process_resp_return_bytes_with_serialize_false"}',
            headers={"Content-Type": "application/json; charset=utf-8"})
    assert api._process_resp("", mock_resp) == b'{"name": "test_Platform_process_resp_return_bytes_with_serialize_false"}'


def test_Platform_process_resp_return_dictionary():
    """
    Check the response processing returns a dictionary for JSON content.
    """
    api = cruds.Client(host="https://localhost")
    mock_resp = urllib3.HTTPResponse(
            body=b'{"name": "test_Platform_process_resp_return_dictionary"}',
            headers={"Content-Type": "application/json; charset=utf-8"},
            status=399)
    assert api._process_resp("", mock_resp) == {"name": "test_Platform_process_resp_return_dictionary"}


def test_Platform_raise_status_399():
    """
    Check the response return code of 399 doesn't raise an exceptions.
    """
    api = cruds.Client(host="https://localhost")
    mock_resp = urllib3.HTTPResponse(body=b'{"name": "test"}', status=399)
    api._process_resp("", mock_resp)


def test_Platform_raise_status_400():
    """
    Check the response status code 400 raises an exception.
    """
    api = cruds.Client(host="https://localhost")
    mock_resp = urllib3.HTTPResponse(body=b'{"name": "test"}', status=400)
    with pytest.raises(urllib3.exceptions.HTTPError):
        api._process_resp("", mock_resp)


def test_Platform_raise_status_500():
    """
    Check the response status code 500 raises an exception.
    """
    api = cruds.Client(host="https://localhost")
    api = cruds.Client(host="https://localhost")
    mock_resp = urllib3.HTTPResponse(body=b'{"name": "test"}', status=500)
    with pytest.raises(urllib3.exceptions.HTTPError):
        api._process_resp("", mock_resp)


def test_Platform_raise_status_whitelist():
    """
    Check the response status code 400 doesn't raises an exception when whitelisted.
    """
    api = cruds.Client(host="https://localhost")
    api = cruds.Client(host="https://localhost", retries=0)
    api.status_whitelist.append(400)
    mock_resp = urllib3.HTTPResponse(body=b'{"name": "test"}', status=400)
    api._process_resp("", mock_resp)
