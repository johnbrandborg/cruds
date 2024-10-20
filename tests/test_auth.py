"""
Tests for Auth components in CRUDs
"""

import json
from time import time
from unittest import mock

from urllib3.response import HTTPResponse

from cruds.auth import OAuth2

access_token: str = "MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3"
refresh_token: str = "IwOGYzYTlmM2YxOTQ5MGE3YmNmMDFkNTVk"

access_token_response: bytes = json.dumps(
    {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 60,
        "scope": "api",
    }
).encode("utf-8")

access_token_response_with_refresh_token: bytes = json.dumps(
    {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 60,
        "refresh_token": refresh_token,
        "scope": "api",
    }
).encode("utf-8")


def test_OAuth2_empty_state():
    """
    Ensure the state of a new OAuth2 instance is empty
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    assert auth._state == {}


def test_OAuth2_access_token_cached():
    """
    If the token has been cached in the Class state, and it's valid to use then
    don't make a request to the server. Just return the access token.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    auth._state = {
        "access_token": access_token,
        "created": int(time()),
        "token_type": "Bearer",
        "expires_in": 60,
        "scope": "api",
    }

    assert auth.is_valid()

    with mock.patch("urllib3.request") as mock_request:
        token: str = auth.access_token()

    assert token == access_token
    mock_request.assert_not_called()


def test_OAuth2_access_token_request():
    """
    If the token has not been cached in the Class state, then the client credientials
    grant type request should be made to the server.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    mock_resp = HTTPResponse(
        access_token_response,
        status=200,
    )

    with mock.patch("urllib3.request", return_value=mock_resp) as mock_request:
        token: str = auth.access_token()

    assert token == access_token

    mock_request.assert_called_with(
        "POST",
        "https://localhost/token",
        body="grant_type=client_credentials&scope=api",
        headers={
            "authorization": "Basic MTIzOkFCQw==",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        },
        redirect=False,
    )


def test_OAuth2_access_token_request_with_password_grant_type():
    """
    If the token has not been cached in the Class state, then the password grant
    type request should be made to the server, because the username and password
    has been supplied.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        username="john",
        password="sdas8329d",
    )

    mock_resp = HTTPResponse(
        access_token_response,
        status=200,
    )

    with mock.patch("urllib3.request", return_value=mock_resp) as mock_request:
        token: str = auth.access_token()

    assert token == access_token

    mock_request.assert_called_with(
        "POST",
        "https://localhost/token",
        body="grant_type=password&scope=api&username=john&password=sdas8329d",
        headers={
            "authorization": "Basic MTIzOkFCQw==",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        },
        redirect=False,
    )


def test_OAuth2_access_token_refresh():
    """
    If the token is invalid and has a refresh token, then the refresh token grant
    request should be made to the server.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    mock_resp = HTTPResponse(
        access_token_response_with_refresh_token,
        status=200,
    )

    with mock.patch("urllib3.request", return_value=mock_resp) as mock_request:
        token: str = auth.access_token()

    assert token == access_token
    auth._state["expires_in"] = 0

    with mock.patch("urllib3.request", return_value=mock_resp) as mock_request:
        token: str = auth.access_token()

    assert token == access_token

    mock_request.assert_called_with(
        "POST",
        "https://localhost/token",
        body=f"grant_type=refresh_token&refresh_token={refresh_token}",
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        },
        redirect=False,
    )
