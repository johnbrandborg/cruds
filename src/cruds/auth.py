"""
Complex authentication flows used to gain access with the CRUDs Client
"""

import json
import logging
import secrets
from time import time
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Dict, Any, Optional, Tuple

import urllib3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from .core import AuthABC
from .exception import OAuthAccessTokenError, OAuthStateError

logger = logging.getLogger(__name__)

TOKEN_REFRESH_LEAD_TIME = 30


class OAuth2(AuthABC):
    """
    A client for the OAuth 2.0 specification, supporting access token using the
    'Client Credientials', 'Password', and 'Authorization Code' grant types.
    """

    def __init__(
        self,
        url: str,
        client_id: str,
        client_secret: str,
        scope: str,
        authorization_details=None,
        username=None,
        password=None,
        encryption_key: Optional[str] = None,
        # Authorization Code flow parameters
        authorization_url: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        state_length: int = 32,
    ) -> None:
        """
        Arguments
        ---------
        url: str
            The url name of the OAuth2 platform.
        client_id: str
            The ID for the client authentication.
        client_secret: str
            The Secret for the client authentication.
        scope: str
            The scope required that the token will have access too.
        authorization_details: list(dict)
            Fine-grained parameters for Rich Authorization Request (RAR)
        username: str (optional)
            Username used for 'Password' grant type.
        password: str (optional)
            Password used for 'Password' grant type.
        encryption_key: str (optional)
            Key for encrypting token state. If not provided, a key will be derived
            from client_secret. For production use, provide a strong encryption key.
        authorization_url: str (optional)
            Authorization endpoint URL for Authorization Code flow.
        redirect_uri: str (optional)
            Redirect URI for Authorization Code flow.
        state_length: int (optional)
            Length of the state parameter for CSRF protection (default: 32).
        """
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.authorization_details = authorization_details
        self.username = username
        self.password = password
        self.authorization_url = authorization_url
        self.redirect_uri = redirect_uri
        self.state_length = state_length

        # Initialize encryption
        self._fernet = self._initialize_encryption(encryption_key)
        self._encrypted_state = b""

        # State parameter for CSRF protection
        self._pending_state: Optional[str] = None

    def _initialize_encryption(self, encryption_key: Optional[str] = None) -> Fernet:
        """
        Initialize encryption using provided key or derive from client_secret.

        Args:
            encryption_key: Optional encryption key. If not provided, derived from client_secret.

        Returns:
            Fernet cipher instance for encryption/decryption
        """
        if encryption_key:
            # Use provided key
            key = base64.urlsafe_b64encode(encryption_key.encode()[:32].ljust(32, b"0"))
        else:
            # Derive key from client_secret (fallback for backward compatibility)
            salt = b"cruds_oauth_salt"  # Fixed salt for deterministic key derivation
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.client_secret.encode()))

        return Fernet(key)

    def _generate_state_parameter(self) -> str:
        """
        Generate a cryptographically secure state parameter for CSRF protection.

        Returns:
            A secure random state string
        """
        return secrets.token_urlsafe(self.state_length)

    def _validate_state_parameter(self, received_state: str) -> bool:
        """
        Validate the received state parameter against the stored pending state.

        Args:
            received_state: The state parameter received from the authorization server

        Returns:
            True if state is valid, False otherwise
        """
        if not self._pending_state:
            logger.warning("No pending state parameter found")
            return False

        if received_state != self._pending_state:
            logger.warning("State parameter mismatch - possible CSRF attack")
            return False

        # Clear the pending state after successful validation
        self._pending_state = None
        return True

    def get_authorization_url(
        self, additional_params: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate the authorization URL for the Authorization Code flow.

        Args:
            additional_params: Additional parameters to include in the authorization URL

        Returns:
            The complete authorization URL with state parameter

        Raises:
            RuntimeError: If authorization_url or redirect_uri is not configured
        """
        if not self.authorization_url or not self.redirect_uri:
            raise RuntimeError(
                "Authorization Code flow requires both authorization_url and redirect_uri to be configured"
            )

        # Generate state parameter for CSRF protection
        state = self._generate_state_parameter()
        self._pending_state = state

        # Build authorization parameters
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": state,
        }

        # Add authorization details if provided
        if self.authorization_details is not None and isinstance(
            self.authorization_details, list
        ):
            params["authorization_details"] = json.dumps(self.authorization_details)
        elif self.authorization_details is not None:
            params["authorization_details"] = self.authorization_details

        # Add additional parameters
        if additional_params:
            params.update(additional_params)

        # Build the authorization URL
        query_string = urlencode(params)
        authorization_url = f"{self.authorization_url}?{query_string}"

        logger.debug(f"Generated authorization URL with state parameter: {state}")
        return authorization_url

    def exchange_code_for_token(self, authorization_code: str, state: str) -> str:
        """
        Exchange authorization code for access token (Authorization Code flow).

        Args:
            authorization_code: The authorization code received from the authorization server
            state: The state parameter received from the authorization server

        Returns:
            The access token

        Raises:
            RuntimeError: If state parameter validation fails
            OAuthAccessTokenError: If token exchange fails
        """
        # Validate state parameter for CSRF protection
        if not self._validate_state_parameter(state):
            raise OAuthStateError("Invalid state parameter - possible CSRF attack")

        logger.debug("Exchanging authorization code for access token")

        # Prepare token exchange request
        fields = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri,
        }

        # Setup Authentication
        request_headers = urllib3.make_headers(
            basic_auth=f"{self.client_id}:{self.client_secret}"
        )
        request_headers["Content-Type"] = (
            "application/x-www-form-urlencoded; charset=utf-8"
        )

        # Make request to the token endpoint
        response = urllib3.request(
            "POST",
            self.url,
            body=urlencode(fields),
            headers=request_headers,
            redirect=False,
        )

        # Handle response
        if 400 <= response.status < 499:
            msg: str = response.json().get("error_description", "Unknown")
            raise OAuthAccessTokenError(msg)

        if not 200 <= response.status < 299:
            # Try to decode error message, fallback to raw data
            try:
                error_message = response.data.decode("utf-8")
            except UnicodeDecodeError:
                error_message = str(response.data)

            error_msg: str = (
                f"Error with status code {response.status}",
                f" Message: {error_message}",
            )
            raise urllib3.exceptions.HTTPError(error_msg)

        # Store the token response
        access_token = response.json()
        access_token["created"] = int(time())
        self._state = access_token

        logger.debug("Successfully exchanged authorization code for access token")
        return access_token.get("access_token", "")

    def parse_authorization_response(self, redirect_url: str) -> Tuple[str, str]:
        """
        Parse the authorization response from the redirect URL.

        Args:
            redirect_url: The full redirect URL received from the authorization server

        Returns:
            Tuple of (authorization_code, state)

        Raises:
            RuntimeError: If the redirect URL is invalid or missing required parameters
        """
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)

        # Check for error response first
        if "error" in query_params:
            error = query_params["error"][0]
            error_description = query_params.get("error_description", ["Unknown"])[0]
            raise OAuthAccessTokenError(
                f"Authorization failed: {error} - {error_description}"
            )

        # Extract authorization code
        if "code" not in query_params:
            raise RuntimeError("Authorization code not found in redirect URL")
        authorization_code = query_params["code"][0]

        # Extract state parameter
        if "state" not in query_params:
            raise RuntimeError("State parameter not found in redirect URL")
        state = query_params["state"][0]

        return authorization_code, state

    def _encrypt_state(self, state: Dict[str, Any]) -> bytes:
        """
        Encrypt the state dictionary.

        Args:
            state: Dictionary containing token state

        Returns:
            Encrypted bytes
        """
        if not state:
            return b""

        state_json = json.dumps(state)
        return self._fernet.encrypt(state_json.encode("utf-8"))

    def _decrypt_state(self, encrypted_data: bytes) -> Dict[str, Any]:
        """
        Decrypt the state dictionary.

        Args:
            encrypted_data: Encrypted state data

        Returns:
            Decrypted state dictionary
        """
        if not encrypted_data:
            return {}

        try:
            decrypted_data = self._fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode("utf-8"))
        except Exception as e:
            logger.warning(f"Failed to decrypt state: {e}")
            return {}

    @property
    def _state(self) -> Dict[str, Any]:
        """Get decrypted state."""
        return self._decrypt_state(self._encrypted_state)

    @_state.setter
    def _state(self, value: Dict[str, Any]) -> None:
        """Set encrypted state."""
        self._encrypted_state = self._encrypt_state(value)

    def access_token(self) -> str:
        if self.is_valid():
            logging.debug("OAuth Token is still valid")
            return self._state["access_token"]

        logging.debug("Retrieving OAuth token")

        # Determine if a refresh_token needs to be used.
        if refresh_token := self._state.get("refresh_token"):
            logging.debug("Use refresh token to renew access token")
            fields = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
            request_headers = urllib3.make_headers()
        else:
            fields = {
                "grant_type": "client_credentials",
                "scope": self.scope,
            }

            # Setup Authentication
            request_headers = urllib3.make_headers(
                basic_auth=f"{self.client_id}:{self.client_secret}"
            )

        # Support Password Grant Type in 2.0
        if self.username is not None and self.password is not None:
            fields["grant_type"] = "password"
            fields["username"] = self.username
            fields["password"] = self.password

        # Rich Authorization Request (RAR)
        if self.authorization_details is not None and isinstance(
            self.authorization_details, list
        ):
            fields["authorization_details"] = json.dumps(self.authorization_details)
        elif self.authorization_details is not None:
            fields["authorization_details"] = self.authorization_details

        request_headers["Content-Type"] = (
            "application/x-www-form-urlencoded; charset=utf-8"
        )

        # Make request to the Server
        response = urllib3.request(
            "POST",
            self.url,
            body=urlencode(fields),
            headers=request_headers,
            redirect=False,
        )

        # Confirm status is ok to proceed further
        if 400 <= response.status < 499:
            msg: str = response.json().get("error_description", "Unknown")
            raise OAuthAccessTokenError(msg)

        if not 200 <= response.status < 299:
            # Try to decode error message, fallback to raw data
            try:
                error_message = response.data.decode("utf-8")
            except UnicodeDecodeError:
                error_message = str(response.data)

            error_msg: str = (
                f"Error with status code {response.status}",
                f"Message: {error_message}",
            )
            raise urllib3.exceptions.HTTPError(error_msg)

        access_token = response.json()
        access_token["created"] = int(time())
        self._state = access_token

        # Check if the token is valid
        return self._state["access_token"] if self.is_valid() else ""

    def is_valid(self) -> bool:
        state: dict = self._state

        if state == {}:
            return False

        if "access_token" not in state or state.get("token_type", "") != "Bearer":
            raise RuntimeError("Auth state is missing critical information")

        if "expires_in" not in state:
            return True

        return int(state["created"] + state["expires_in"]) > (
            int(time()) + TOKEN_REFRESH_LEAD_TIME
        )

    def clear_state(self) -> None:
        """
        Clear the encrypted state, effectively logging out the user.
        """
        self._encrypted_state = b""
        self._pending_state = None
        logger.debug("OAuth state cleared")
