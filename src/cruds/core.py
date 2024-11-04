"""
Clients that can be used for easily accessing RESTful APIs
"""

import abc
from base64 import b64encode
import logging
from json.decoder import JSONDecodeError
import sys
from typing import Final

from typing import Any, Dict, Union
from urllib.parse import urlencode

import certifi
import urllib3

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT: Final = 300.0


class AuthABC(metaclass=abc.ABCMeta):
    """
    An Abstract Base Class that is used for implement the required interface
    that is used for Authentcation by the Client class.
    """

    @abc.abstractmethod
    def access_token(self) -> str:
        """
        Retrives the access token from the server, and performs refreshing the
        token if supported by the protocol.

        :return: access token as a string
        """
        pass

    @abc.abstractmethod
    def is_valid(self) -> bool:
        """
        Check if an access token is valid and hasn't expired yet.

        :return: true if token is valid, otherwise false
        """
        pass


class Client:
    """
    Represents an platform interface that supports CRUD operations as methods.

    Data supplied as Dictionaries are automatically serialised and deserialized
    as JSON. All parameters are key-word values, and positional arguments are
    not accepted.

    Instance Attributes
    -------------------
    status_ignore: set
        A set of status codes to ignore by instances with raise for status
        enabled.

    Methods
    -------
    create:
        Makes a POST request to the API Server
    read:
        Makes a GET request to the API Server
    update:
        Makes a PATCH or PUT request to the API Server
    delete:
        Makes a DELETE request to the API Server
    """

    def __init__(
        self,
        host: str,
        auth=None,
        manager=None,
        timeout=DEFAULT_TIMEOUT,
        raise_status=True,
        retries=4,
        backoff_factor=0.9,
        retry_status_codes=(504, 503, 502, 500, 429, 425, 408),
        serialize=True,
        verify_ssl=True,
    ) -> None:
        """
        Arguments
        ---------
        host: str
            The host name of the API server connections will be made too.
        auth: str, tuple, cruds.auth.Auth (optional)
            A bearer token can be supplied, or a tuple with the username
            and password. CRUDs includes more complex authentication using
            the AuthABC Classes under the `cruds.auth` module.
        manager: urllib3.PoolManager, urllib3.ProxyManager (optional)
            You can supply a PoolManager with custom configuration.
        timeout: float (optional)
            How long to wait before the connection is considered to be
            taking to long and cancelled.
        raise_status: bool (optional)
            If a status code of 400-599 is returned in a response will an
            exception is raised.
        retries: int (optional)
            How many times to retry connecting to the host.
        backoff_factor: float (optional)
            How much delay should be added with each retry.
        retry_status_codes: typle[int] (optional)
            Status codes that will trigger retries.
            (default is (504, 503, 502, 500, 429, 425))
        serialize: boolaen (optional)
            Serialize and Deserialize dictionaires for data sent and received.
            (default is True)
        verify_ssl: boolean (optional)
            Verify the SSL certificate with Certificate Authorities.
            (default is True)
        """
        self.host: str = host if host.endswith("/") else host + "/"
        self.serialize: bool = serialize
        logger.info(
            "API Operation Timeout(sec): %s, Raises Exceptions on status: %s",
            timeout,
            raise_status,
        )

        self.raise_status: bool = raise_status
        self.status_ignore: set = set()

        if isinstance(manager, (urllib3.PoolManager, urllib3.ProxyManager)):
            logger.info("Using supplied URLLib3 PoolManager or ProxyManager")
            self.manager = manager
        else:
            # Setup Retries
            if retries:
                logger.info(
                    "Retries: %s attempts (backoff factor %s) for status codes %s",
                    retries,
                    backoff_factor,
                    ", ".join([str(i) for i in retry_status_codes]),
                )

                retry = urllib3.Retry(
                    total=retries,
                    status_forcelist=retry_status_codes,
                    backoff_factor=backoff_factor,
                )
            else:
                logger.info("Retries: Disabled")
                retry = False

            # Create PoolManager
            self.manager = urllib3.PoolManager(
                cert_reqs="CERT_REQUIRED" if verify_ssl else "CERT_NONE",
                ca_certs=certifi.where(),
                retries=retry,
                timeout=timeout,
            )

        # Setup Headers (Authentication)
        self.request_headers = urllib3.HTTPHeaderDict()

        if isinstance(auth, str):
            self.request_headers.add("Authorization", f"Bearer {auth}")
            logger.info("Token authentication setup")
        elif isinstance(auth, (list, tuple)) and len(auth) == 2:
            self.request_headers.add(
                "Authorization",
                "Basic " + b64encode(":".join(auth).encode("UTF-8")).decode("UTF-8"),
            )
            logger.info("Basic authentication setup")
        elif isinstance(auth, AuthABC):
            self.auth: AuthABC = auth
            self._check_auth()
            logger.info(f"{auth.__class__.__name__} authentication setup")
        else:
            logger.info("No authentication setup")

    def create(
        self,
        uri: str,
        data: dict,
        params: Union[Dict[Any, Any], None] = None,
    ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Create request to the API, and returns the response.

        The HTTP method used is POST, and the data can be either a dictionary
        that is serialised to JSON or bytes and strings that will be sent
        without serialisation.

        For POST requests parameters are encoded into the URL.
        https://urllib3.readthedocs.io/en/stable/user-guide.html#query-parameters

        Parameters
        ----------
        uri : str
            The URI to be used to with the connection to the API
        data : dict or bytes or string
            Payload to be sent to the API
        params : dict, optional
            Parameters to be added to the URI

        Returns
        -------
        dict if the response is JSON, otherwise bytes
        """
        url: str = self.host + uri.lstrip("/")
        safe_params: str = f"?{urlencode(params)}" if params else ""
        method: str = "POST"
        logger.info(f"API Create Operation to {url}")

        self._check_auth()
        if self.serialize:
            response = self.manager.request(
                method, url + safe_params, headers=self.request_headers, json=data
            )
        else:
            response = self.manager.request(
                method, url + safe_params, body=data, headers=self.request_headers
            )

        return self._process_resp(method, response)

    def read(
        self,
        uri: str,
        params: Union[Dict[Any, Any], None] = None,
    ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Retrieve request to the API, and returns the response

        The HTTP method used is GET.

        Parameters
        ----------
        uri : str
            The URI to be used to with the connection to the API
        params : dict, optional
            Parameters to be added to the URI

        Returns
        -------
        dict if the response is JSON, otherwise bytes
        """
        url: str = self.host + uri.lstrip("/")
        method: str = "GET"
        logger.info(f"API Retrieve Operation to {url}")

        self._check_auth()
        response = self.manager.request(
            method, url, fields=params, headers=self.request_headers
        )
        return self._process_resp(method, response)

    def update(
        self,
        uri: str,
        data: Union[Dict[Any, Any], str],
        params: Union[Dict[Any, Any], None] = None,
        replace: bool = False,
    ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Update request to the API, and returns the response.

        The HTTP method used is PATCH (or PUT with replace enabled), and the data
        can be either a dictionary that is serialised to JSON or bytes and
        strings that will be sent without serialisation.

        For PUT requests parameters are encoded into the URL.
        https://urllib3.readthedocs.io/en/stable/user-guide.html#query-parameters

        Parameters
        ----------
        uri : str
            The URI to be used to with the connection to the API
        data : dict or bytes or string
            Payload to be sent to the API
        params : dict, optional
            Parameters to be added to the URI
        replace : bool, optional
            Requests a full replacement of the entire entity. Uses PUT Method.

        Returns
        -------
        dict if the response is JSON, otherwise bytes
        """
        url: str = self.host + uri.lstrip("/")
        safe_params: str = f"?{urlencode(params)}" if params else ""
        method: str = "PUT" if replace else "PATCH"
        logger.info(f"API Update Operation to {url}")

        self._check_auth()
        if self.serialize:
            response = self.manager.request(
                method, url + safe_params, headers=self.request_headers, json=data
            )
        else:
            response = self.manager.request(
                method, url + safe_params, body=data, headers=self.request_headers
            )

        return self._process_resp(method, response)

    def delete(
        self, uri: str, params: Union[Dict[Any, Any], None] = None
    ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Delete request to the API, and returns the response

        Parameters
        ----------
        uri : str
            The URI to be used to with the connection to the API
        params : dict, optional
            Parameters to be added to the URI

        Returns
        -------
        dict if the response is JSON, otherwise bytes
        """
        url: str = self.host + uri.lstrip("/")
        method: str = "DELETE"
        logger.info(f"API Delete Operation to {url}")

        self._check_auth()
        response = self.manager.request(
            method, self.host + uri, fields=params, headers=self.request_headers
        )
        return self._process_resp(method, response)

    def _process_resp(
        self,
        method: str,
        response: urllib3.response.BaseHTTPResponse,
    ) -> Union[Dict[Any, Any], bytes]:
        """
        Processes the Responce from URLLib3 request in a standardize manner, and
        displays information.
        """
        logger.info(
            f"Method: {method}, Status Code: {response.status}, "
            f"Memory: {sys.getsizeof(response.data)} Bytes"
        )

        if self.raise_status and response.status not in self.status_ignore:
            if 400 <= response.status < 500:
                error_type = "Client"
            elif 500 <= response.status < 600:
                error_type = "Server"
            else:
                error_type = None

            if error_type:
                msg: str = (
                    f"{error_type} Error with status code {response.status}"
                    f" Message: {response.data.decode('utf-8')}"
                )
                raise urllib3.exceptions.HTTPError(msg)

        if self.serialize:
            if "application/json" in response.headers.get("Content-Type", ""):
                return response.json()

            logger.warning(
                "Response content type is not declared as JSON but serialize is enabled"
            )
            try:
                return response.json()
            except JSONDecodeError:
                return response.data

        return response.data

    def _check_auth(self):
        if (
            hasattr(self, "auth")
            and isinstance(self.auth, AuthABC)
            and not self.auth.is_valid()
        ):
            self.request_headers["Authorization"] = "Bearer " + self.auth.access_token()
