"""
Pytests for Clients in RESTful Client2
"""

import json
from unittest import mock
import pytest
import urllib3

import restful_client2


@pytest.fixture
def crud_api():
    """ Creates a CRUD Interface without response processing"""
    api = restful_client2.CRUD(host="https://localhost", retries=0)
    mock_resp = urllib3.HTTPResponse(body="{'type': 'test'}")
    api._http.request = mock.Mock(return_value=mock_resp)
    api._process_resp = lambda method, resp: resp
    return api


def test_CRUD_create_operation(crud_api):
    """ Check the Create Operation formats the request properly """
    sample = {"test_name": "test_CRUD_create_operation"}
    resp = crud_api.create("test", data=sample)

    crud_api._http.request.assert_called_with("POST",
                                              "https://localhost/test",
                                              body=json.dumps(sample),
                                              timeout=20.0)
    assert resp.data == "{'type': 'test'}"


def test_CRUD_read_operation(crud_api):
    """ Check the Read Operation formats the request properly """
    resp = crud_api.read("test")

    crud_api._http.request.assert_called_with("GET",
                                              "https://localhost/test",
                                              fields=None,
                                              timeout=20.0)
    assert resp.data == "{'type': 'test'}"


def test_CRUD_update_operation(crud_api):
    """ Check the Update Operation formats the request properly """
    sample = {"test_name": "test_CRUD_update_operation"}
    resp = crud_api.update("test", data=sample)

    crud_api._http.request.assert_called_with("PUT",
                                              "https://localhost/test",
                                              body=json.dumps(sample),
                                              timeout=20.0)
    assert resp.data == "{'type': 'test'}"


def test_CRUD_update_operation_with_patch(crud_api):
    """ Check the Update Operation formats the request properly """
    sample = {"test_name": "test_CRUD_update_operation"}
    resp = crud_api.update("test", data=sample, with_patch=True)

    crud_api._http.request.assert_called_with("PATCH",
                                              "https://localhost/test",
                                              body=json.dumps(sample),
                                              timeout=20.0)
    assert resp.data == "{'type': 'test'}"


def test_CRUD_delete_operation(crud_api):
    """ Check the Delete Operation formats the request properly """
    resp = crud_api.delete("test")

    crud_api._http.request.assert_called_with("DELETE",
                                              "https://localhost/test",
                                              fields=None,
                                              timeout=20.0)
    assert resp.data == "{'type': 'test'}"
