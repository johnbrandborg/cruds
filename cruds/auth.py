import logging
import random
import string
from time import time

import urllib3


logger= logging.getLogger(__name__)

TOKEN_REFRESH_LEAD_TIME = 30


def _state_gen(length=16) -> str:
    return ''.join(
        random.choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits
        ) for _ in range(length)
    )


class OAuth:
    def __init__(
            self,
            server: str,
            client_id: str,
            client_secret: str,
            scope: str
        ) -> None:
        self.server = server
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope

        self._state = None

    @property
    def token(self) -> str:
        if self._state and self.is_valid:
            logging.debug("OAuth Token is still valid")
            return self._state["access_token"]

        logging.debug("Retrieving OAuth token")

        request_headers = urllib3.make_headers(
                basic_auth=f"{self.client_id}:{self.client_secret}"
        )
        request_headers["Content-Type"] = "application/x-www-form-urlencoded; charset=utf-8"

        token_resp = urllib3.request(
            "POST",
            self.server,
            body=f"grant_type=client_credentials&scope={self.scope}",
            headers=request_headers,
            redirect=False,
        )

        jsn = token_resp.json()

        jsn["expires_on"] = int(time() + jsn["expires_in"])
        self._state = jsn

        return jsn["access_token"]

    @property
    def is_valid(self, time_key="expires_on") -> bool:
        """
        Check if an OAuth token is valid and hasn't expired yet.

        :param sp_token: dict with properties of OAuth token
        :param time_key: name of the key that holds the time of expiration
        :return: true if token is valid, false otherwise
        """

        if self._state is None:
            return False

        if self._state and (
                "access_token" not in self._state
                    or self._state.get("token_type", "") != "Bearer"
                ):
            raise RuntimeError(f"OAuth state is missing critical information")

        if self._state and time_key not in self._state:
            raise RuntimeError(f"Can't find time key '{time_key}' in OAuth state")

        return int(self._state[time_key]) > (int(time()) + TOKEN_REFRESH_LEAD_TIME)
