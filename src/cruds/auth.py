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
import hashlib
import hmac

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
        self._encryption_key: Optional[str] = self._initialize_encryption(
            encryption_key
        )
        self._encrypted_state = b""

        # State parameter for CSRF protection
        self._pending_state: Optional[str] = None

    def _initialize_encryption(
        self, encryption_key: Optional[str] = None
    ) -> Optional[str]:
        """
        Initialize encryption using provided key.

        Args:
            encryption_key: Optional encryption key. If not provided, encryption will be
                          handled dynamically with random salts.

        Returns:
            Encryption key string, or None if using dynamic encryption
        """
        if encryption_key:
            # Use provided key
            return encryption_key
        else:
            # For client_secret-based encryption, we use dynamic salts
            # No single key is created here
            return None

    def _generate_encryption_key(self, salt: bytes) -> bytes:
        """
        Generate encryption key from client_secret using the provided salt.

        Args:
            salt: The salt to use for key derivation

        Returns:
            Encryption key bytes
        """
        kdf = hashlib.pbkdf2_hmac(
            "sha256",
            self.client_secret.encode(),
            salt,
            100000,
        )
        return kdf

    def _encrypt_with_key(self, data: bytes, key: bytes) -> bytes:
        """
        Encrypt data using a simple XOR-based encryption with HMAC for integrity.

        Args:
            data: Data to encrypt
            key: Encryption key

        Returns:
            Encrypted data with HMAC
        """
        # Generate a random IV
        iv = secrets.token_bytes(16)

        # Pad data to be a multiple of 16 bytes
        padding_length = 16 - (len(data) % 16)
        padded_data = data + bytes([padding_length] * padding_length)

        # Simple XOR encryption with key cycling
        encrypted = bytearray()
        for i, byte in enumerate(padded_data):
            key_byte = key[i % len(key)]
            encrypted.append(byte ^ key_byte)

        # Add HMAC for integrity
        h = hmac.new(key, iv + bytes(encrypted), hashlib.sha256)
        hmac_digest = h.digest()

        # Return: IV + encrypted_data + HMAC
        return iv + bytes(encrypted) + hmac_digest

    def _decrypt_with_key(self, encrypted_data: bytes, key: bytes) -> bytes:
        """
        Decrypt data using the same XOR-based encryption.

        Args:
            encrypted_data: Encrypted data with IV and HMAC
            key: Encryption key

        Returns:
            Decrypted data

        Raises:
            ValueError: If HMAC verification fails
        """
        if len(encrypted_data) < 48:  # IV(16) + HMAC(32) + at least 1 byte of data
            raise ValueError("Encrypted data too short")

        # Extract components
        iv = encrypted_data[:16]
        hmac_digest = encrypted_data[-32:]
        encrypted = encrypted_data[16:-32]

        # Verify HMAC
        h = hmac.new(key, iv + encrypted, hashlib.sha256)
        expected_hmac = h.digest()
        if not hmac.compare_digest(hmac_digest, expected_hmac):
            raise ValueError("HMAC verification failed")

        # Decrypt using XOR
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            key_byte = key[i % len(key)]
            decrypted.append(byte ^ key_byte)

        # Remove padding
        padding_length = decrypted[-1]
        if padding_length > 16 or padding_length == 0:
            raise ValueError("Invalid padding")

        return bytes(decrypted[:-padding_length])

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

    def _handle_http_response(self, response) -> None:
        """
        Handle HTTP response and raise appropriate exceptions for errors.

        Args:
            response: The HTTP response from urllib3

        Raises:
            OAuthAccessTokenError: For 4xx client errors
            urllib3.exceptions.HTTPError: For other HTTP errors
        """
        if 400 <= response.status < 499:
            msg: str = response.json().get("error_description", "Unknown")
            raise OAuthAccessTokenError(msg)

        if not 200 <= response.status < 299:
            # Try to decode error message, fallback to raw data
            try:
                error_message = response.data.decode("utf-8")
            except UnicodeDecodeError:
                error_message = str(response.data)

            raise urllib3.exceptions.HTTPError(
                f"Error with status code {response.status} Message: {error_message}"
            )

    def _add_authorization_details(self, params: Dict[str, str]) -> None:
        """
        Add authorization details to the parameters if provided.

        Args:
            params: Dictionary to add authorization details to
        """
        if self.authorization_details is not None and isinstance(
            self.authorization_details, list
        ):
            params["authorization_details"] = json.dumps(self.authorization_details)
        elif self.authorization_details is not None:
            params["authorization_details"] = self.authorization_details

    def _make_oauth_request(
        self, fields: Dict[str, str], use_auth: bool = True
    ) -> Dict[str, Any]:
        """
        Make an OAuth request to the token endpoint.

        Args:
            fields: The form fields to send in the request
            use_auth: Whether to include basic authentication headers

        Returns:
            The JSON response from the server

        Raises:
            OAuthAccessTokenError: For 4xx client errors
            urllib3.exceptions.HTTPError: For other HTTP errors
        """
        # Setup Authentication
        if use_auth:
            request_headers = urllib3.make_headers(
                basic_auth=f"{self.client_id}:{self.client_secret}"
            )
        else:
            request_headers = urllib3.make_headers()

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
        self._handle_http_response(response)

        # Return the JSON response
        return response.json()

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
        self._add_authorization_details(params)

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

        # Make request to the token endpoint
        access_token = self._make_oauth_request(fields)

        # Store the token response
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
        Encrypt the state dictionary with a random salt.

        Args:
            state: Dictionary containing token state

        Returns:
            Encrypted bytes with salt prefix (for dynamic encryption) or without (for fixed key)
        """
        if not state:
            return b""

        state_json = json.dumps(state)
        state_bytes = state_json.encode("utf-8")

        if self._encryption_key is not None:
            # Use fixed encryption key
            key = hashlib.sha256(self._encryption_key.encode()).digest()
            return self._encrypt_with_key(state_bytes, key)
        else:
            # Use dynamic encryption with random salt
            salt = secrets.token_bytes(16)
            key = self._generate_encryption_key(salt)
            encrypted_data = self._encrypt_with_key(state_bytes, key)
            # Return salt + encrypted data
            return salt + encrypted_data

    def _decrypt_state(self, encrypted_data: bytes) -> Dict[str, Any]:
        """
        Decrypt the state dictionary using the stored salt.

        Args:
            encrypted_data: Encrypted state data with salt prefix (for dynamic encryption) or without (for fixed key)

        Returns:
            Decrypted state dictionary
        """
        if not encrypted_data:
            return {}

        try:
            if self._encryption_key is not None:
                # Use fixed encryption key
                key = hashlib.sha256(self._encryption_key.encode()).digest()
                decrypted_data = self._decrypt_with_key(encrypted_data, key)
                return json.loads(decrypted_data.decode("utf-8"))
            else:
                # Use dynamic encryption with salt prefix
                # Try to decrypt with old fixed salt first for backward compatibility
                try:
                    old_salt = b"cruds_oauth_salt"
                    key = self._generate_encryption_key(old_salt)
                    decrypted_data = self._decrypt_with_key(encrypted_data, key)
                    return json.loads(decrypted_data.decode("utf-8"))
                except Exception:
                    # If old salt fails, try new format with salt prefix
                    if len(encrypted_data) >= 16:
                        # Extract salt (first 16 bytes) and encrypted data
                        salt = encrypted_data[:16]
                        actual_encrypted_data = encrypted_data[16:]

                        # Generate key with the stored salt
                        key = self._generate_encryption_key(salt)

                        # Decrypt the data
                        decrypted_data = self._decrypt_with_key(
                            actual_encrypted_data, key
                        )
                        return json.loads(decrypted_data.decode("utf-8"))
                    else:
                        # Data too short, can't be valid
                        raise ValueError("Encrypted data too short")
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
            logger.debug("OAuth Token is still valid")
            return self._state["access_token"]

        logger.debug("Retrieving OAuth token")

        # Determine if a refresh_token needs to be used.
        if refresh_token := self._state.get("refresh_token"):
            logger.debug("Use refresh token to renew access token")
            fields = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
            # Refresh token requests don't use basic auth
            access_token = self._make_oauth_request(fields, use_auth=False)
        else:
            fields = {
                "grant_type": "client_credentials",
                "scope": self.scope,
            }

            # Support Password Grant Type in 2.0
            if self.username is not None and self.password is not None:
                fields["grant_type"] = "password"
                fields["username"] = self.username
                fields["password"] = self.password

            # Rich Authorization Request (RAR)
            self._add_authorization_details(fields)

            # Make request to the Server
            access_token = self._make_oauth_request(fields)

        # Store the token response
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
