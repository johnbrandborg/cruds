"""
Clients that can be used for easily accessing RESTful APIs
"""

import json
import logging
import sys
from typing import Any, Dict, Iterator, List, Union
from urllib.parse import urlencode

import urllib3

logger = logging.getLogger(__name__)


class CRUD:
    """
    A simple RESTful Client that supports CRUD operations as methods.
    Data supplied as Dictionaries are automatically serialised as JSON. All
    parameters are key-word values, and positional arguments are not accepted.
    """

    status_whitelist: List[int] = []

    def __init__(self,
                 *,
                 host: str,
                 auth=None,
                 manager=None,
                 timeout=20.0,
                 raise_status=True,
                 retries=4,
                 backoff_factor=0.9,
                 retry_status_codes=(504, 503, 502, 500, 429),
                 ):
        self.host = host if host.endswith("/") else host + "/"

        logger.info("API Operation Timeout(sec): %s, Raises Exceptions on status: %s",
                    timeout,
                    raise_status)

        self.raise_status = raise_status
        self.timeout = timeout

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

            self._http = urllib3.PoolManager(retries=retry)

            if isinstance(auth, str):
                self._http.headers["Authorization"] = f"Bearer {auth}"
                logger.info("Token authentication setup")
            elif isinstance(auth, (list, tuple)) and len(auth) == 2:
                self._http.headers = urllib3.make_headers(basic_auth=":".join(auth))
                logger.info("Basic authentication setup")
            else:
                logger.info("No authentication setup")

        self._http.headers["Content-Type"] = "application/json"

    def create(self,
               uri: str,
               data: dict,
               params: Union[Dict[Any, Any], None] = None,
               ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Create request to the API, and returns the response
        """
        url = self.host + uri + (f"?{urlencode(params)}" if params else "")
        method = "POST"
        logger.info(f"API Create Operation to {url}")

        if not isinstance(data, (str, bytes)):
            data = json.dumps(data)

        response = self._http.request(method,
                                      url,
                                      body=data,
                                      timeout=self.timeout)
        return self._process_resp(method, response)

    def read(self,
             uri: str,
             fields: Union[Dict[Any, Any], None] = None,
             ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Retrieve request to the API, and returns the response
        """
        url = self.host + uri
        method = "GET"
        logger.info(f"API Retrieve Operation to {url}")

        response = self._http.request(method,
                                      url,
                                      fields=fields,
                                      timeout=self.timeout)
        return self._process_resp(method, response)

    def update(self,
               uri: str,
               data: Union[Dict[Any, Any], str],
               params: Union[Dict[Any, Any], None] = None,
               with_patch: bool = False,
               ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Update request to the API, and returns the response
        """
        url = self.host + uri + (f"?{urlencode(params)}" if params else "")
        method = "PATCH" if with_patch else "PUT"
        logger.info(f"API Update Operation to {url}")

        if not isinstance(data, (str, bytes)):
            data = json.dumps(data)

        response = self._http.request(method,
                                      url,
                                      body=data,
                                      timeout=self.timeout)
        return self._process_resp(method, response)

    def delete(self,
               uri: str,
               fields: Union[Dict[Any, Any], None] = None
               ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Delete request to the API, and returns the response
        """
        url = self.host + uri
        method = "DELETE"
        logger.info(f"API Delete Operation to {url}")

        response = self._http.request(method,
                                      self.host + uri,
                                      fields=fields,
                                      timeout=self.timeout)
        return self._process_resp(method, response)

    def _process_resp(self, method, response) -> Union[Dict[Any, Any], bytes]:
        """
        Processes the Responce from HTTP Requests in a standardize manner, and
        displays information.
        """
        logger.debug(
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

        try:
            return json.loads(response.data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return response.data
