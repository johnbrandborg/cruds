"""
Tests for Auth components in CRUDs
"""

import json
from time import time
from unittest import mock
import pytest

from urllib3.response import HTTPResponse

from cruds.auth import OAuth2
from cruds.exception import OAuthAccessTokenError, OAuthStateError
import urllib3
import hashlib
import hmac
import secrets

access_token: str = "MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3"
refresh_token: str = "IwOGYzYTlmM2YxOTQ5MGE3YmNmMDFkNTVk"
authorization_code: str = "abc123def456"

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

authorization_code_response: bytes = json.dumps(
    {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
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


def test_OAuth2_authorization_code_flow_initialization():
    """
    Test that OAuth2 can be initialized with Authorization Code flow parameters
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
        state_length=64,
    )

    assert auth.authorization_url == "https://localhost/authorize"
    assert auth.redirect_uri == "https://localhost/callback"
    assert auth.state_length == 64
    assert auth._pending_state is None


def test_OAuth2_generate_authorization_url():
    """
    Test that authorization URL is generated with state parameter
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )

    auth_url = auth.get_authorization_url()

    # Verify URL structure
    assert auth_url.startswith("https://localhost/authorize?")
    assert "response_type=code" in auth_url
    assert "client_id=123" in auth_url
    assert "redirect_uri=" in auth_url
    assert "scope=api" in auth_url
    assert "state=" in auth_url

    # Verify state parameter was generated and stored
    assert auth._pending_state is not None
    assert len(auth._pending_state) >= 32  # Default state length


def test_OAuth2_generate_authorization_url_with_additional_params():
    """
    Test that authorization URL includes additional parameters
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )

    additional_params = {"prompt": "consent", "access_type": "offline"}
    auth_url = auth.get_authorization_url(additional_params)

    assert "prompt=consent" in auth_url
    assert "access_type=offline" in auth_url


def test_OAuth2_generate_authorization_url_with_authorization_details():
    """
    Test that authorization URL includes authorization details
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
        authorization_details=[{"type": "permissions", "operation": "read"}],
    )

    auth_url = auth.get_authorization_url()

    assert "authorization_details=" in auth_url


def test_OAuth2_generate_authorization_url_missing_config():
    """
    Test that authorization URL generation fails without proper configuration
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    with pytest.raises(RuntimeError, match="Authorization Code flow requires"):
        auth.get_authorization_url()


def test_OAuth2_parse_authorization_response():
    """
    Test parsing of authorization response with valid parameters
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )

    # Generate authorization URL to set pending state
    auth.get_authorization_url()
    pending_state = auth._pending_state

    # Create redirect URL
    redirect_url = (
        f"https://localhost/callback?code={authorization_code}&state={pending_state}"
    )

    code, state = auth.parse_authorization_response(redirect_url)

    assert code == authorization_code
    assert state == pending_state


def test_OAuth2_parse_authorization_response_missing_code():
    """
    Test parsing fails when authorization code is missing
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    redirect_url = "https://localhost/callback?state=test_state"

    with pytest.raises(RuntimeError, match="Authorization code not found"):
        auth.parse_authorization_response(redirect_url)


def test_OAuth2_parse_authorization_response_missing_state():
    """
    Test parsing fails when state parameter is missing
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    redirect_url = f"https://localhost/callback?code={authorization_code}"

    with pytest.raises(RuntimeError, match="State parameter not found"):
        auth.parse_authorization_response(redirect_url)


def test_OAuth2_parse_authorization_response_error():
    """
    Test parsing fails when authorization server returns an error
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    redirect_url = "https://localhost/callback?error=access_denied&error_description=User%20denied%20access"

    with pytest.raises(
        OAuthAccessTokenError, match="Authorization failed: access_denied"
    ):
        auth.parse_authorization_response(redirect_url)


def test_OAuth2_exchange_code_for_token():
    """
    Test exchanging authorization code for access token
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )

    # Generate authorization URL to set pending state
    auth.get_authorization_url()
    pending_state = auth._pending_state

    mock_resp = HTTPResponse(
        authorization_code_response,
        status=200,
    )

    with mock.patch("urllib3.request", return_value=mock_resp) as mock_request:
        token = auth.exchange_code_for_token(authorization_code, pending_state)

    assert token == access_token

    mock_request.assert_called_with(
        "POST",
        "https://localhost/token",
        body=f"grant_type=authorization_code&code={authorization_code}&redirect_uri=https%3A%2F%2Flocalhost%2Fcallback",
        headers={
            "authorization": "Basic MTIzOkFCQw==",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        },
        redirect=False,
    )


def test_OAuth2_exchange_code_for_token_invalid_state():
    """
    Test that token exchange fails with invalid state parameter
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )

    # Generate authorization URL to set pending state
    auth.get_authorization_url()

    # Try to exchange with wrong state
    with pytest.raises(OAuthStateError, match="Invalid state parameter"):
        auth.exchange_code_for_token(authorization_code, "wrong_state")


def test_OAuth2_exchange_code_for_token_no_pending_state():
    """
    Test that token exchange fails when no pending state exists
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )

    # No pending state set
    with pytest.raises(OAuthStateError, match="Invalid state parameter"):
        auth.exchange_code_for_token(authorization_code, "some_state")


def test_OAuth2_state_parameter_reuse_prevention():
    """
    Test that state parameter can only be used once
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )

    # Generate authorization URL to set pending state
    auth.get_authorization_url()
    pending_state = auth._pending_state

    mock_resp = HTTPResponse(
        authorization_code_response,
        status=200,
    )

    with mock.patch("urllib3.request", return_value=mock_resp):
        # First use should succeed
        auth.exchange_code_for_token(authorization_code, pending_state)

    # State should be cleared after successful use
    assert auth._pending_state is None

    # Second use should fail
    with pytest.raises(OAuthStateError, match="Invalid state parameter"):
        auth.exchange_code_for_token(authorization_code, pending_state)


def test_OAuth2_clear_state_clears_pending_state():
    """
    Test that clear_state also clears pending state
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )

    # Generate authorization URL to set pending state
    auth.get_authorization_url()
    assert auth._pending_state is not None

    # Clear state
    auth.clear_state()

    # Both encrypted state and pending state should be cleared
    assert auth._state == {}
    assert auth._pending_state is None


def test_OAuth2_encryption_with_custom_key():
    """
    Test that encryption works with a custom encryption key
    """
    custom_key = "my-secret-encryption-key-32-chars-long"
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        encryption_key=custom_key,
    )

    test_state = {"access_token": "test_token", "token_type": "Bearer"}
    auth._state = test_state

    # Verify the state is encrypted (not plain text)
    assert auth._encrypted_state != b""
    assert b"test_token" not in auth._encrypted_state

    # Verify decryption works
    assert auth._state == test_state


def test_OAuth2_encryption_without_custom_key():
    """
    Test that encryption works when deriving key from client_secret
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    test_state = {"access_token": "test_token", "token_type": "Bearer"}
    auth._state = test_state

    # Verify the state is encrypted (not plain text)
    assert auth._encrypted_state != b""
    assert b"test_token" not in auth._encrypted_state

    # Verify decryption works
    assert auth._state == test_state


def test_OAuth2_clear_state():
    """
    Test that clear_state method properly clears the encrypted state
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    test_state = {"access_token": "test_token", "token_type": "Bearer"}
    auth._state = test_state

    # Verify state is set
    assert auth._state == test_state

    # Clear state
    auth.clear_state()

    # Verify state is cleared
    assert auth._state == {}
    assert auth._encrypted_state == b""


def test_OAuth2_decryption_error_handling():
    """
    Test that decryption errors are handled gracefully
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    # Set invalid encrypted data
    auth._encrypted_state = b"invalid-encrypted-data"

    # Should return empty dict and log warning
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

    # Set expired state with refresh token
    expired_state = {
        "access_token": access_token,
        "created": int(time()),
        "token_type": "Bearer",
        "expires_in": 0,  # Expired
        "refresh_token": refresh_token,
        "scope": "api",
    }
    auth._state = expired_state

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


def test_OAuth2_access_token_400_error():
    """
    Should raise OAuthAccessTokenError for 400-499 response.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    mock_resp = HTTPResponse(b'{"error_description": "Bad Request"}', status=400)
    mock_resp.json = lambda: {"error_description": "Bad Request"}
    with mock.patch("urllib3.request", return_value=mock_resp):
        with pytest.raises(OAuthAccessTokenError):
            auth.access_token()


def test_OAuth2_access_token_non_2xx_error():
    """
    Should raise HTTPError for non-2xx, non-400-499 response.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    mock_resp = HTTPResponse(b"Internal Error", status=500)
    mock_resp.json = lambda: {}
    with mock.patch("urllib3.request", return_value=mock_resp):
        with pytest.raises(urllib3.exceptions.HTTPError):
            auth.access_token()


def test_OAuth2_access_token_with_authorization_details_list():
    """
    Should handle authorization_details as a list.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_details=[{"type": "test"}],
    )
    mock_resp = HTTPResponse(access_token_response, status=200)
    with mock.patch("urllib3.request", return_value=mock_resp) as mock_request:
        token = auth.access_token()
    assert token == access_token
    assert "authorization_details" in mock_request.call_args[1]["body"]


def test_OAuth2_access_token_with_authorization_details_str():
    """
    Should handle authorization_details as a string.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_details="test-string",
    )
    mock_resp = HTTPResponse(access_token_response, status=200)
    with mock.patch("urllib3.request", return_value=mock_resp) as mock_request:
        token = auth.access_token()
    assert token == access_token
    assert "authorization_details" in mock_request.call_args[1]["body"]


def test_OAuth2_is_valid_missing_access_token():
    """
    Should raise RuntimeError if access_token or token_type is missing.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    auth._state = {"token_type": "Bearer"}
    with pytest.raises(RuntimeError):
        auth.is_valid()
    auth._state = {"access_token": "foo", "token_type": "NotBearer"}
    with pytest.raises(RuntimeError):
        auth.is_valid()


def test_OAuth2_is_valid_no_expires_in():
    """
    If the token doesn't have an expires_in field, it should be considered valid.
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
        "scope": "api",
    }

    assert auth.is_valid()


def test_OAuth2_access_token_unicode_decode_error():
    """
    Test that Unicode decode errors in error messages are handled gracefully.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    # Create response with non-UTF-8 bytes
    mock_resp = HTTPResponse(
        body=b"\xff\xfe\x00\x00",  # Invalid UTF-8 bytes
        status=500,
    )

    with mock.patch("urllib3.request", return_value=mock_resp):
        with pytest.raises(urllib3.exceptions.HTTPError) as exc_info:
            auth.access_token()

    # Should not crash and should include the raw bytes in the error message
    assert "Error with status code 500" in str(exc_info.value)
    assert "Message:" in str(exc_info.value)


def test_OAuth2_access_token_utf8_error_message():
    """
    Test that valid UTF-8 error messages are handled correctly.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    # Create response with valid UTF-8 error message
    error_message = "Invalid client credentials"
    mock_resp = HTTPResponse(body=error_message.encode("utf-8"), status=500)

    with mock.patch("urllib3.request", return_value=mock_resp):
        with pytest.raises(urllib3.exceptions.HTTPError) as exc_info:
            auth.access_token()

    # Should include the decoded error message
    assert "Error with status code 500" in str(exc_info.value)
    assert error_message in str(exc_info.value)


def test_OAuth2_is_valid_token_expired():
    """
    Test that is_valid returns False when token is expired.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    # Set expired state
    expired_state = {
        "access_token": access_token,
        "created": int(time()) - 100,  # Created 100 seconds ago
        "token_type": "Bearer",
        "expires_in": 60,  # Expires in 60 seconds, but created 100 seconds ago
        "scope": "api",
    }
    auth._state = expired_state
    assert not auth.is_valid()


def test_OAuth2_is_valid_token_expiring_soon():
    """
    Test that is_valid returns False when token expires within the lead time.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    # Set state that expires within the lead time (30 seconds)
    expiring_soon_state = {
        "access_token": access_token,
        "created": int(time()),
        "token_type": "Bearer",
        "expires_in": 25,  # Expires in 25 seconds, less than 30 second lead time
        "scope": "api",
    }
    auth._state = expiring_soon_state
    assert not auth.is_valid()


def test_OAuth2_is_valid_token_valid_with_lead_time():
    """
    Test that is_valid returns True when token expires after the lead time.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    # Set state that expires after the lead time
    valid_state = {
        "access_token": access_token,
        "created": int(time()),
        "token_type": "Bearer",
        "expires_in": 60,  # Expires in 60 seconds, more than 30 second lead time
        "scope": "api",
    }
    auth._state = valid_state
    assert auth.is_valid()


def test_OAuth2_exchange_code_for_token_400_error():
    """
    Test that exchange_code_for_token raises OAuthAccessTokenError for 400-499 responses.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )
    # Generate authorization URL to set pending state
    auth.get_authorization_url()
    pending_state = auth._pending_state
    mock_resp = HTTPResponse(
        b'{"error_description": "Invalid authorization code"}', status=400
    )
    mock_resp.json = lambda: {"error_description": "Invalid authorization code"}
    with mock.patch("urllib3.request", return_value=mock_resp):
        with pytest.raises(OAuthAccessTokenError, match="Invalid authorization code"):
            auth.exchange_code_for_token(authorization_code, pending_state)


def test_OAuth2_exchange_code_for_token_500_error():
    """
    Test that exchange_code_for_token raises HTTPError for 500+ responses.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )
    # Generate authorization URL to set pending state
    auth.get_authorization_url()
    pending_state = auth._pending_state
    mock_resp = HTTPResponse(b"Internal Server Error", status=500)
    with mock.patch("urllib3.request", return_value=mock_resp):
        with pytest.raises(urllib3.exceptions.HTTPError):
            auth.exchange_code_for_token(authorization_code, pending_state)


def test_OAuth2_exchange_code_for_token_missing_access_token():
    """
    Test that exchange_code_for_token handles missing access_token in response.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )
    # Generate authorization URL to set pending state
    auth.get_authorization_url()
    pending_state = auth._pending_state
    # Response without access_token
    mock_resp = HTTPResponse(
        json.dumps({"token_type": "Bearer", "expires_in": 3600}).encode("utf-8"),
        status=200,
    )
    with mock.patch("urllib3.request", return_value=mock_resp):
        token = auth.exchange_code_for_token(authorization_code, pending_state)
        assert token == ""  # Should return empty string when access_token is missing


def test_OAuth2_encryption_key_too_short():
    """
    Test that encryption works with a key shorter than 32 characters.
    """
    short_key = "short-key"
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        encryption_key=short_key,
    )
    test_state = {"access_token": "test_token", "token_type": "Bearer"}
    auth._state = test_state
    assert auth._encrypted_state != b""
    assert auth._state == test_state


def test_OAuth2_encryption_key_too_long():
    """
    Test that encryption works with a key longer than 32 characters.
    """
    long_key = "this-is-a-very-long-encryption-key-that-exceeds-32-characters"
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        encryption_key=long_key,
    )
    test_state = {"access_token": "test_token", "token_type": "Bearer"}
    auth._state = test_state
    assert auth._encrypted_state != b""
    assert auth._state == test_state


def test_OAuth2_encryption_key_with_special_characters():
    """
    Test that encryption works with keys containing special characters.
    """
    special_key = "key-with-!@#$%^&*()_+-=[]{}|;':\",./<>?"
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        encryption_key=special_key,
    )
    test_state = {"access_token": "test_token", "token_type": "Bearer"}
    auth._state = test_state
    assert auth._encrypted_state != b""
    assert auth._state == test_state


def test_OAuth2_access_token_refresh_with_new_refresh_token():
    """
    Test that refresh token flow updates the stored refresh token.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    # Set expired state with old refresh token
    old_refresh_token = "old_refresh_token"
    expired_state = {
        "access_token": "old_access_token",
        "created": int(time()) - 100,
        "token_type": "Bearer",
        "expires_in": 0,  # Expired
        "refresh_token": old_refresh_token,
        "scope": "api",
    }
    auth._state = expired_state
    # Mock response with new refresh token
    new_refresh_token = "new_refresh_token"
    refresh_response = json.dumps(
        {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": new_refresh_token,
            "scope": "api",
        }
    ).encode("utf-8")
    mock_resp = HTTPResponse(refresh_response, status=200)
    with mock.patch("urllib3.request", return_value=mock_resp):
        token = auth.access_token()
    assert token == access_token
    assert auth._state["refresh_token"] == new_refresh_token
    assert auth._state["refresh_token"] != old_refresh_token


def test_OAuth2_access_token_refresh_without_new_refresh_token():
    """
    Test that refresh token flow works when new response doesn't include refresh token.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    # Set expired state with refresh token
    expired_state = {
        "access_token": "old_access_token",
        "created": int(time()) - 100,
        "token_type": "Bearer",
        "expires_in": 0,  # Expired
        "refresh_token": refresh_token,
        "scope": "api",
    }
    auth._state = expired_state
    # Mock response without refresh token (some OAuth providers don't return new refresh tokens)
    refresh_response = json.dumps(
        {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "api",
        }
    ).encode("utf-8")
    mock_resp = HTTPResponse(refresh_response, status=200)
    with mock.patch("urllib3.request", return_value=mock_resp):
        token = auth.access_token()
    assert token == access_token
    assert "refresh_token" not in auth._state


def test_OAuth2_access_token_password_grant_with_authorization_details():
    """
    Test that password grant type works with authorization details.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        username="john",
        password="password123",
        authorization_details=[{"type": "permissions", "operation": "read"}],
    )
    mock_resp = HTTPResponse(access_token_response, status=200)
    with mock.patch("urllib3.request", return_value=mock_resp) as mock_request:
        token = auth.access_token()
    assert token == access_token
    request_body = mock_request.call_args[1]["body"]
    assert "authorization_details" in request_body
    assert "permissions" in request_body


def test_OAuth2_access_token_client_credentials_with_authorization_details():
    """
    Test that client credentials grant type works with authorization details.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_details="custom-auth-details",
    )
    mock_resp = HTTPResponse(access_token_response, status=200)
    with mock.patch("urllib3.request", return_value=mock_resp) as mock_request:
        token = auth.access_token()
    assert token == access_token
    request_body = mock_request.call_args[1]["body"]
    assert "authorization_details" in request_body
    assert "custom-auth-details" in request_body


def test_OAuth2_generate_authorization_url_with_custom_state_length():
    """
    Test that authorization URL generation works with custom state length.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
        state_length=64,
    )
    auth_url = auth.get_authorization_url()
    assert auth_url.startswith("https://localhost/authorize?")
    assert "state=" in auth_url
    assert auth._pending_state is not None


def test_OAuth2_validate_state_parameter_with_none():
    """
    Test that state validation fails when no pending state exists.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    assert not auth._validate_state_parameter("any_state")


def test_OAuth2_validate_state_parameter_with_mismatch():
    """
    Test that state validation fails when state doesn't match.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )
    auth.get_authorization_url()
    original_state = auth._pending_state
    assert not auth._validate_state_parameter("wrong_state")
    assert auth._pending_state == original_state


def test_OAuth2_validate_state_parameter_success():
    """
    Test that state validation succeeds with correct state.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )
    auth.get_authorization_url()
    original_state = auth._pending_state
    assert auth._validate_state_parameter(original_state)
    assert auth._pending_state is None


def test_OAuth2_encrypt_state_empty():
    """
    Test that encrypting empty state returns empty bytes.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    encrypted = auth._encrypt_state({})
    assert encrypted == b""


def test_OAuth2_decrypt_state_empty():
    """
    Test that decrypting empty data returns empty dict.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    decrypted = auth._decrypt_state(b"")
    assert decrypted == {}


def test_OAuth2_decrypt_state_invalid_json():
    """
    Test that decrypting invalid JSON data returns empty dict.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    invalid_data = b"invalid-encrypted-data"
    decrypted = auth._decrypt_state(invalid_data)
    assert decrypted == {}


def test_OAuth2_state_property_setter_none():
    """
    Test that setting state to None works correctly.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    auth._state = None
    assert auth._state == {}


def test_OAuth2_authorization_url_with_complex_authorization_details():
    """
    Test that authorization URL handles complex authorization details.
    """
    complex_auth_details = [
        {
            "type": "payment_initiation",
            "locations": ["https://example.com/payments"],
            "instructedAmount": {"currency": "EUR", "amount": "123.50"},
        },
        {
            "type": "account_information",
            "locations": ["https://example.com/accounts"],
            "balances": ["EUR"],
        },
    ]
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
        authorization_details=complex_auth_details,
    )
    auth_url = auth.get_authorization_url()
    assert "authorization_details=" in auth_url
    assert "%22type%22" in auth_url  # URL encoded quote


def test_OAuth2_access_token_returns_empty_string_on_invalid():
    """
    Test that access_token raises RuntimeError when token is invalid after refresh
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    # Mock response with invalid token (missing access_token)
    mock_response = mock.Mock()
    mock_response.status = 200
    mock_response.json.return_value = {"token_type": "Bearer", "expires_in": 60}
    mock_response.data = b"invalid response"
    with mock.patch("urllib3.request", return_value=mock_response):
        with pytest.raises(
            RuntimeError, match="Auth state is missing critical information"
        ):
            auth.access_token()


def test_OAuth2_authorization_details_string_not_list():
    """
    Test authorization URL generation when authorization_details is a string (not list)
    This covers line 188 in auth.py
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
        authorization_details='{"type": "permissions", "operation": "read"}',
    )
    auth_url = auth.get_authorization_url()
    # Should be URL-encoded JSON string
    assert (
        "authorization_details=%7B%22type%22%3A+%22permissions%22%2C+%22operation%22%3A+%22read%22%7D"
        in auth_url
    )


def test_OAuth2_exchange_code_for_token_unicode_decode_error():
    """
    Covers UnicodeDecodeError handling in exchange_code_for_token (lines 255-256).
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="id",
        client_secret="secret",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
    )
    auth.get_authorization_url()
    state = auth._pending_state

    class MockResponse:
        status = 500
        data = b"\xff\xfe\xfd"

        def json(self):
            raise Exception("Should not be called")

    def mock_request(*args, **kwargs):
        return MockResponse()

    with mock.patch("urllib3.request", mock_request):
        with pytest.raises(urllib3.exceptions.HTTPError) as exc_info:
            auth.exchange_code_for_token("code", state)

        assert (
            str(exc_info.value)
            == "Error with status code 500 Message: b'\\xff\\xfe\\xfd'"
        )


def test_OAuth2_access_token_unicode_decode_error_in_main_flow():
    """
    Test UnicodeDecodeError handling in main access_token method
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )
    mock_response = mock.Mock()
    mock_response.status = 500
    mock_response.data = b"\xff\xfe\xfd"
    mock_response.json.side_effect = Exception("JSON decode failed")
    with mock.patch("urllib3.request", return_value=mock_response):
        with pytest.raises(urllib3.exceptions.HTTPError) as exc_info:
            auth.access_token()

        assert (
            str(exc_info.value)
            == "Error with status code 500 Message: b'\\xff\\xfe\\xfd'"
        )


def test_OAuth2_authorization_details_empty_list():
    """
    Test authorization URL generation when authorization_details is an empty list
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        authorization_url="https://localhost/authorize",
        redirect_uri="https://localhost/callback",
        authorization_details=[],
    )
    auth_url = auth.get_authorization_url()
    # Should be URL-encoded []
    assert "authorization_details=%5B%5D" in auth_url


def test_OAuth2_dynamic_salt_encryption():
    """
    Test that dynamic salt encryption works correctly and produces different results
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    test_state = {"access_token": "test_token", "token_type": "Bearer"}

    # Encrypt the same state multiple times
    auth._state = test_state
    first_encryption = auth._encrypted_state

    auth._state = test_state
    second_encryption = auth._encrypted_state

    # Verify that each encryption produces different results (due to random salt)
    assert first_encryption != second_encryption

    # Verify that both can be decrypted correctly
    auth._encrypted_state = first_encryption
    assert auth._state == test_state

    auth._encrypted_state = second_encryption
    assert auth._state == test_state


def test_OAuth2_salt_storage_format():
    """
    Test that salt is properly stored with encrypted data
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    test_state = {"access_token": "test_token", "token_type": "Bearer"}
    auth._state = test_state

    # Verify that encrypted data has salt prefix (16 bytes + encrypted data)
    assert len(auth._encrypted_state) > 16

    # Verify that the first 16 bytes are the salt
    salt = auth._encrypted_state[:16]
    encrypted_data = auth._encrypted_state[16:]

    # Verify that we can decrypt using the extracted salt
    key = auth._generate_encryption_key(salt)
    decrypted_data = auth._decrypt_with_key(encrypted_data, key)
    decrypted_state = json.loads(decrypted_data.decode("utf-8"))

    assert decrypted_state == test_state


def test_OAuth2_backward_compatibility_old_salt():
    """
    Test backward compatibility with old fixed salt format
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    # Create encrypted data using old fixed salt format (simulating original implementation)
    old_salt = b"cruds_oauth_salt"
    key = hashlib.pbkdf2_hmac(
        "sha256",
        auth.client_secret.encode(),
        old_salt,
        100000,
    )

    # Use the new encryption method
    test_state = {"access_token": "old_token", "token_type": "Bearer"}
    old_encrypted_data = auth._encrypt_with_key(
        json.dumps(test_state).encode("utf-8"), key
    )

    # Debug: Check the length of the encrypted data
    print(f"Old encrypted data length: {len(old_encrypted_data)}")
    print(f"Is < 16: {len(old_encrypted_data) < 16}")

    # Set the old format encrypted data (no salt prefix)
    auth._encrypted_state = old_encrypted_data

    # Verify that it can be decrypted correctly
    # Note: This should work because the decryption method checks for old format
    decrypted_state = auth._state
    assert decrypted_state == test_state


def test_OAuth2_encryption_key_generation():
    """
    Test that encryption key generation works correctly with different salts
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    # Test with different salts
    salt1 = b"test_salt_1_16b"
    salt2 = b"test_salt_2_16b"

    key1 = auth._generate_encryption_key(salt1)
    key2 = auth._generate_encryption_key(salt2)

    # Verify that different salts produce different keys
    assert key1 != key2

    # Verify that keys are valid encryption keys (32 bytes)
    assert len(key1) == 32
    assert len(key2) == 32


def test_OAuth2_encryption_with_salt():
    """
    Test that encryption can be performed with different salts
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    salt = b"test_salt_16bytes"
    key = auth._generate_encryption_key(salt)

    # Verify that encryption and decryption work
    test_data = b"test_data"
    encrypted = auth._encrypt_with_key(test_data, key)
    decrypted = auth._decrypt_with_key(encrypted, key)

    assert decrypted == test_data


def test_OAuth2_decryption_error_handling_with_salt():
    """
    Test that decryption errors are handled gracefully with salt format
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    # Test with invalid salt format (too short)
    auth._encrypted_state = b"short"
    assert auth._state == {}

    # Test with invalid salt format (wrong salt)
    invalid_salt = b"invalid_salt_16b"
    key = auth._generate_encryption_key(invalid_salt)
    invalid_encrypted = auth._encrypt_with_key(b"test", key)

    # Create data with wrong salt
    auth._encrypted_state = invalid_salt + invalid_encrypted
    assert auth._state == {}


def test_OAuth2_encryption_modes_comparison():
    """
    Test that both encryption modes work correctly
    """
    # Test dynamic encryption (no encryption_key)
    auth_dynamic = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    # Test fixed encryption (with encryption_key)
    auth_fixed = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
        encryption_key="my-secret-encryption-key-32-chars-long",
    )

    test_state = {"access_token": "test_token", "token_type": "Bearer"}

    # Test dynamic encryption
    auth_dynamic._state = test_state
    assert auth_dynamic._state == test_state
    assert len(auth_dynamic._encrypted_state) > 16  # Has salt prefix

    # Test fixed encryption
    auth_fixed._state = test_state
    assert auth_fixed._state == test_state
    # Fernet output is typically longer than 16 bytes, but doesn't have salt prefix
    # The key difference is that dynamic encryption has salt + encrypted data
    # while fixed encryption just has encrypted data

    # Verify that they produce different encrypted formats
    assert auth_dynamic._encrypted_state != auth_fixed._encrypted_state


def test_OAuth2_decrypt_with_key_invalid_padding():
    """
    Test that _decrypt_with_key raises ValueError for invalid padding values.
    This specifically tests line 199 in auth.py.
    """
    auth = OAuth2(
        url="https://localhost/token",
        client_id="123",
        client_secret="ABC",
        scope="api",
    )

    # Create a valid key
    key = auth._generate_encryption_key(b"test_salt_16bytes")

    # Test case 1: padding_length > 16
    # Create data with invalid padding (17 bytes of padding with value 17)
    test_data = b"test_data"
    invalid_padded_data = test_data + bytes(
        [17] * 17
    )  # 17 bytes of padding with value 17

    # Encrypt this data manually to bypass HMAC issues
    iv = secrets.token_bytes(16)
    encrypted = bytearray()
    for i, byte in enumerate(invalid_padded_data):
        key_byte = key[i % len(key)]
        encrypted.append(byte ^ key_byte)

    # Create HMAC for the encrypted data
    h = hmac.new(key, iv + bytes(encrypted), hashlib.sha256)
    hmac_digest = h.digest()

    # Combine: IV + encrypted + HMAC
    invalid_encrypted_data = iv + bytes(encrypted) + hmac_digest

    # This should raise ValueError due to invalid padding (> 16)
    with pytest.raises(ValueError, match="Invalid padding"):
        auth._decrypt_with_key(invalid_encrypted_data, key)

    # Test case 2: padding_length == 0
    # Create data with zero padding (16 bytes of padding with value 0)
    zero_padded_data = test_data + bytes([0] * 16)  # 16 bytes of padding with value 0

    # Encrypt this data manually
    iv_zero = secrets.token_bytes(16)
    encrypted_zero = bytearray()
    for i, byte in enumerate(zero_padded_data):
        key_byte = key[i % len(key)]
        encrypted_zero.append(byte ^ key_byte)

    # Create HMAC for the encrypted data
    h_zero = hmac.new(key, iv_zero + bytes(encrypted_zero), hashlib.sha256)
    hmac_digest_zero = h_zero.digest()

    # Combine: IV + encrypted + HMAC
    zero_encrypted_data = iv_zero + bytes(encrypted_zero) + hmac_digest_zero

    # This should raise ValueError due to zero padding
    with pytest.raises(ValueError, match="Invalid padding"):
        auth._decrypt_with_key(zero_encrypted_data, key)
