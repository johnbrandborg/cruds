"""
Complex authentication flows used to gain access with the CRUDs Client
"""

import json
import logging
from time import time
from urllib.parse import urlencode

import urllib3

from .core import AuthABC
from .exception import OAuthAccessTokenError

logger = logging.getLogger(__name__)

TOKEN_REFRESH_LEAD_TIME = 30


class OAuth2(AuthABC):
    """
    A client for the OAuth 2.0 specification, supporting access token using the
    'Client Credientials' and 'Password' grant type.
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
        """
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.authorization_details = authorization_details
        self.username = username
        self.password = password
        self._state = {}

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
            msg: str = (
                f"Error with status code {response.status}"
                f" Message: {response.data.decode('utf-8')}"
            )
            raise urllib3.exceptions.HTTPError(msg)

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
