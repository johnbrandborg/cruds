"""
Clients that can be used for easily accessing RESTful APIs
"""

import abc
from email.message import Message
import logging
from json.decoder import JSONDecodeError
from pathlib import Path
import re
import sys
from typing import Any, Final
from urllib.parse import unquote, unquote_to_bytes, urlencode, urlsplit

import certifi
import urllib3

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT: Final = 300.0

_FieldValue = str | bytes | tuple[str, str | bytes] | tuple[str, str | bytes, str]


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
    download:
        Downloads a response to the local filesystem
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

                retry_config = urllib3.Retry(
                    total=retries,
                    status_forcelist=retry_status_codes,
                    backoff_factor=backoff_factor,
                    allowed_methods=frozenset(
                        {"GET", "POST", "PUT", "PATCH", "DELETE"}
                    ),
                )
            else:
                logger.info("Retries: Disabled")
                retry_config = False

            # Create PoolManager
            self.manager = urllib3.PoolManager(
                cert_reqs="CERT_REQUIRED" if verify_ssl else "CERT_NONE",
                ca_certs=certifi.where() if verify_ssl else None,
                retries=retry_config,
                timeout=urllib3.Timeout(connect=timeout, read=timeout),
            )

        # Setup Headers (Authentication)
        self.request_headers = urllib3.HTTPHeaderDict()

        if isinstance(auth, str):
            self.request_headers.add("Authorization", f"Bearer {auth}")
            logger.info("Token authentication setup")
        elif isinstance(auth, (list, tuple)) and len(auth) == 2:
            basic_auth_header = urllib3.make_headers(basic_auth=f"{auth[0]}:{auth[1]}")
            self.request_headers.add(
                "Authorization", basic_auth_header["authorization"]
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
        params: dict[Any, Any] | None = None,
        files: dict[str, _FieldValue] | None = None,
    ) -> dict[Any, Any] | bytes:
        """
        Makes a basic Create request to the API, and returns the response.

        The HTTP method used is POST, and the data can be either a dictionary
        that is serialised to JSON or bytes and strings that will be sent
        without serialisation.

        When files is provided, the request is sent as multipart/form-data
        using urllib3's fields parameter. This takes precedence over data
        serialisation.

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
        files : dict, optional
            Multipart form fields passed as urllib3 fields. Values can be
            plain strings/bytes for form data, (filename, data) tuples, or
            (filename, data, content_type) tuples for file uploads.

        Returns
        -------
        dict if the response is JSON, otherwise bytes
        """
        url: str = self.host + uri.lstrip("/")
        safe_params: str = f"?{urlencode(params)}" if params else ""
        method: str = "POST"
        logger.info(f"API Create Operation to {url}")

        self._check_auth()
        response = self._request_with_data(method, url + safe_params, data, files)
        return self._process_resp(method, response)

    def read(
        self,
        uri: str,
        params: dict[Any, Any] | None = None,
    ) -> dict[Any, Any] | bytes:
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

    def download(
        self,
        uri: str,
        path: str | Path | None = None,
        filename: str | None = None,
        params: dict[Any, Any] | None = None,
    ) -> Path:
        """
        Download a response to the local filesystem.

        The filename is taken from the standards-based Content-Disposition
        header, then the final response URL, and finally the optional filename
        argument. The current working directory is used when path is omitted.
        """
        url = self.host + uri.lstrip("/")
        method = "GET"
        destination = Path.cwd() if path is None else Path(path)
        logger.info(f"API Download Operation from {url} to {destination}")

        if not destination.is_dir():
            raise NotADirectoryError(f"Download path is not a directory: {destination}")

        self._check_auth()
        response = self.manager.request(
            method,
            url,
            fields=params,
            headers=self.request_headers,
            preload_content=False,
        )

        try:
            self._raise_for_status(method, response)
            response_url = response.geturl() or url
            response_filename = self._download_filename(
                response.headers.get("Content-Disposition"),
                response_url,
                filename,
            )
            output_path = destination / response_filename

            created = False
            try:
                with output_path.open("xb") as output:
                    created = True
                    for chunk in response.stream(amt=64 * 1024):
                        output.write(chunk)
            except BaseException:
                if created:
                    output_path.unlink(missing_ok=True)
                raise

            return output_path
        finally:
            response.release_conn()

    def update(
        self,
        uri: str,
        data: dict[Any, Any] | str,
        params: dict[Any, Any] | None = None,
        replace: bool = False,
        files: dict[str, _FieldValue] | None = None,
    ) -> dict[Any, Any] | bytes:
        """
        Makes a basic Update request to the API, and returns the response.

        The HTTP method used is PATCH (or PUT with replace enabled), and the data
        can be either a dictionary that is serialised to JSON or bytes and
        strings that will be sent without serialisation.

        When files is provided, the request is sent as multipart/form-data
        using urllib3's fields parameter. This takes precedence over data
        serialisation.

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
        files : dict, optional
            Multipart form fields passed as urllib3 fields. Values can be
            plain strings/bytes for form data, (filename, data) tuples, or
            (filename, data, content_type) tuples for file uploads.

        Returns
        -------
        dict if the response is JSON, otherwise bytes
        """
        url: str = self.host + uri.lstrip("/")
        safe_params: str = f"?{urlencode(params)}" if params else ""
        method: str = "PUT" if replace else "PATCH"
        logger.info(f"API Update Operation to {url}")

        self._check_auth()
        response = self._request_with_data(method, url + safe_params, data, files)
        return self._process_resp(method, response)

    def delete(
        self, uri: str, params: dict[Any, Any] | None = None
    ) -> dict[Any, Any] | bytes:
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
            method, url, fields=params, headers=self.request_headers
        )
        return self._process_resp(method, response)

    def _request_with_data(
        self,
        method: str,
        url: str,
        data: Any,
        files: dict[str, _FieldValue] | None,
    ) -> urllib3.response.BaseHTTPResponse:
        """
        Dispatches an HTTP request with a body payload. Multipart fields take
        precedence, then JSON serialisation, then raw body.
        """
        if files is not None:
            return self.manager.request(
                method, url, fields=files, headers=self.request_headers
            )
        if self.serialize:
            return self.manager.request(
                method, url, headers=self.request_headers, json=data
            )
        return self.manager.request(
            method, url, body=data, headers=self.request_headers
        )

    def _process_resp(
        self,
        method: str,
        response: urllib3.response.BaseHTTPResponse,
    ) -> dict[Any, Any] | bytes:
        """
        Processes the Response from URLLib3 request in a standardized manner, and
        displays information.
        """
        logger.info(
            f"Method: {method}, Status Code: {response.status}, "
            f"Memory: {sys.getsizeof(response.data)} Bytes"
        )

        self._raise_for_status(method, response)

        if self.serialize and response.data is not None:
            content_type = response.headers.get("Content-Type", "").lower()
            is_json_content_type = "application/json" in content_type

            # Try to parse as JSON regardless of content-type
            # This handles APIs that return JSON but don't set the correct content-type
            try:
                return response.json()
            except JSONDecodeError as e:
                if is_json_content_type:
                    logger.warning(f"Failed to parse JSON response: {e}")
                else:
                    logger.debug(
                        f"Response content type '{content_type}' is not JSON and "
                        f"response data could not be parsed as JSON"
                    )
                return response.data

        return response.data

    def _raise_for_status(
        self,
        method: str,
        response: urllib3.response.BaseHTTPResponse,
    ) -> None:
        """Raise an HTTP error according to this client's status policy."""
        if self.raise_status and response.status not in self.status_ignore:
            if 400 <= response.status < 500:
                error_type = "Client"
            elif 500 <= response.status < 600:
                error_type = "Server"
            else:
                error_type = None

            if error_type:
                # Try to decode error message, fallback to raw data
                try:
                    error_message = response.data.decode("utf-8")
                except UnicodeDecodeError:
                    error_message = str(response.data)

                msg: str = (
                    f"{error_type} Error with status code {response.status}"
                    f" Message: {error_message}"
                )
                raise urllib3.exceptions.HTTPError(msg)

    @classmethod
    def _download_filename(
        cls,
        content_disposition: str | None,
        response_url: str,
        fallback: str | None,
    ) -> str:
        """Select and sanitize a filename for a downloaded response."""
        candidates = [
            cls._content_disposition_filename(content_disposition),
            unquote(urlsplit(response_url).path.rsplit("/", 1)[-1]),
            fallback,
        ]
        for candidate in candidates:
            if candidate and (safe_name := cls._sanitize_filename(candidate)):
                return safe_name
        raise ValueError(
            "Download response did not provide a usable filename; "
            "supply filename explicitly"
        )

    @staticmethod
    def _content_disposition_filename(value: str | None) -> str | None:
        """Extract filename* or filename from an RFC 6266 header."""
        if not value:
            return None

        extended = re.search(
            r"(?:^|;)\s*filename\*\s*=\s*(?:\"([^\"]*)\"|([^;]*))",
            value,
            flags=re.IGNORECASE,
        )
        if extended:
            encoded = next(
                part for part in extended.groups() if part is not None
            ).strip()
            try:
                charset, _, encoded_name = encoded.split("'", 2)
                return unquote_to_bytes(encoded_name).decode(charset or "utf-8")
            except (LookupError, UnicodeDecodeError, ValueError):
                pass

        message = Message()
        message["Content-Disposition"] = value
        return message.get_filename()

    @staticmethod
    def _sanitize_filename(value: str) -> str:
        """Remove path and control characters from an advisory filename."""
        basename = value.replace("\\", "/").rsplit("/", 1)[-1]
        basename = "".join(
            character
            for character in basename
            if ord(character) >= 32 and ord(character) != 127
        ).strip()
        return "" if basename in {"", ".", ".."} else basename

    def _check_auth(self):
        if (
            hasattr(self, "auth")
            and isinstance(self.auth, AuthABC)
            and not self.auth.is_valid()
        ):
            self.request_headers["Authorization"] = "Bearer " + self.auth.access_token()
