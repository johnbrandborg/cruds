"""
Clients that can be used for easily accessing RESTful APIs
"""

import logging
import sys
from typing import Any, Dict, List, Union
from urllib.parse import urlencode

import certifi
import urllib3

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 20.0


class Client:
    """
    Represents an platform interface that supports CRUD operations as methods.

    Data supplied as Dictionaries are automatically serialised and deserialized
    as JSON. All parameters are key-word values, and positional arguments are
    not accepted.

    Attributes
    ----------
    status_whitelist : list
        A list of status codes to ignore by instances with raise for status
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

    status_whitelist: List[int] = []

    def __init__(self,
                 *,
                 host: str,
                 auth=None,
                 manager=None,
                 timeout=DEFAULT_TIMEOUT,
                 raise_status=True,
                 retries=4,
                 backoff_factor=0.9,
                 retry_status_codes=(504, 503, 502, 500, 429),
                 serialize=True,
                 verify_ssl=True,
                 ) -> None:
        """
        Constructs all the necessary attributes for the API object.

        Parameters
        ----------
            host: str
                The host name of the API server connections will be made too.
            auth: str or tuple, optional
                A bearer token can be supplied, or a tuple with the username
                and password.
            manager: URLLib3 PoolManager, optional
                You can supply a PoolManager with custom configuration.
            timeout : float, optional
                How long to wait before the connection is considered to be
                taking to long and cancelled.
            raise_status : bool, optional
                If a status code of 400-599 is returned in a response will an
                exception is raised.
            retries : int, optional
                How many times to retry connecting to the host.
            backoff_factor : float, optional
                How much delay should be added with each retry.
            retry_status_codes : typle[int], optional
                Status codes that will trigger retries.
                (default is (504, 503, 502, 429))
            serialize : boolaen, optional
                Serialize and Deserialize dictionaires for data sent and received.
                (default is True)
            verify_ssl : boolean, optional
                Verify the SSL certificate with Certificate Authorities.
                (default is True)
        """
        self.host: str = host if host.endswith("/") else host + "/"
        self.serialize = serialize
        logger.info("API Operation Timeout(sec): %s, Raises Exceptions on status: %s",
                    timeout,
                    raise_status)

        self.raise_status: bool = raise_status
        self.timeout: float = timeout

        if isinstance(manager, urllib3.PoolManager):
            logger.info("Using supplied HTTP Manager")
            self._http = manager
        else:
            if retries:
                logger.info("Retries: %s attempts (backoff factor %s) for status codes %s",
                            retries,
                            backoff_factor,
                            ', '.join([str(i) for i in retry_status_codes]))

                retry = urllib3.Retry(connect=retries,
                                      backoff_factor=backoff_factor,
                                      status_forcelist=retry_status_codes)
            else:
                logger.info("Retries: Disabled")
                retry = False

            self._http = urllib3.PoolManager(
                cert_reqs="CERT_REQUIRED" if verify_ssl else "CERT_NONE",
                ca_certs=certifi.where(),
                retries=retry)

            if isinstance(auth, str):
                self._http.headers["Authorization"] = f"Bearer {auth}"
                logger.info("Token authentication setup")
            elif isinstance(auth, (list, tuple)) and len(auth) == 2:
                self._http.headers = urllib3.make_headers(basic_auth=":".join(auth))
                logger.info("Basic authentication setup")
            else:
                logger.info("No authentication setup")

        self._http.headers["Content-Type"] = "application/json; charset=utf-8"

    def create(self,
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
        url = self.host + uri
        safe_params = f"?{urlencode(params)}" if params else ""
        method = "POST"
        logger.info(f"API Create Operation to {url}")

        if self.serialize and isinstance(data, dict):
            response = self._http.request(method,
                                          url + safe_params,
                                          json=data,
                                          timeout=self.timeout)
        else:
            response = self._http.request(method,
                                          url + safe_params,
                                          body=data,
                                          timeout=self.timeout)

        return self._process_resp(method, response)

    def read(self,
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
        url = self.host + uri
        method = "GET"
        logger.info(f"API Retrieve Operation to {url}")

        response = self._http.request(method,
                                      url,
                                      fields=params,
                                      timeout=self.timeout)
        return self._process_resp(method, response)

    def update(self,
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
        url = self.host + uri
        safe_params = f"?{urlencode(params)}" if params else ""
        method = "PUT" if replace else "PATCH"
        logger.info(f"API Update Operation to {url}")

        if self.serialize and isinstance(data, dict):
            response = self._http.request(method,
                                          url + safe_params,
                                          json=data,
                                          timeout=self.timeout)
        else:
            response = self._http.request(method,
                                          url + safe_params,
                                          body=data,
                                          timeout=self.timeout)

        return self._process_resp(method, response)

    def delete(self,
               uri: str,
               params: Union[Dict[Any, Any], None] = None
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
        url = self.host + uri
        method = "DELETE"
        logger.info(f"API Delete Operation to {url}")

        response = self._http.request(method,
                                      self.host + uri,
                                      fields=params,
                                      timeout=self.timeout)
        return self._process_resp(method, response)

    def _process_resp(
            self,
            method: str,
            response: urllib3.response.BaseHTTPResponse,
            ) -> Union[Dict[Any, Any], bytes]:
        """
        Processes the Responce from HTTP Requests in a standardize manner, and
        displays information.
        """
        logger.info(
            f"Method: {method}, Status Code: {response.status}, "
            f"Data: {sys.getsizeof(response.data)} Bytes"
        )

        if self.raise_status and response.status not in self.status_whitelist:
            if 400 <= response.status < 500:
                error_type = "Client"
            elif 500 <= response.status < 600:
                error_type = "Server"
            else:
                error_type = None

            if error_type:
                msg = f"{error_type} Error with status code {response.status}" \
                      f" Message: {response.data.decode('utf-8')}"
                raise urllib3.exceptions.HTTPError(msg)

        if self.serialize and 'application/json' in response.headers.get('Content-Type', ''):
            return response.json()

        return response.data
