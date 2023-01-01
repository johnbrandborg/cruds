"""
RESTful Client is a CRUD interface that can be used for extending with API specific methods.
"""

import json
import sys
from typing import Any, Dict, Iterator, List, Union
from urllib.parse import urlencode

import urllib3


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

        print(f"API Operation Timeout(sec): {timeout}, Raises Exceptions on status: {raise_status}")
        self.raise_status = raise_status
        self.timeout = timeout

        if isinstance(manager, urllib3.PoolManager):
            print("Using supplied HTTP Manager", end=" ")
            self._http = manager
        else:
            if retries:
                print(
                    f"Retries: {retries} attempts (backoff factor {backoff_factor})",
                    f"for status codes {', '.join([str(i) for i in retry_status_codes])}.",
                )
                retry = urllib3.Retry(connect=retries,
                                      backoff_factor=backoff_factor,
                                      status_forcelist=retry_status_codes)
            else:
                print("Retries: Disabled")
                retry = False

            print("Creating HTTP Manager", end=" ")
            self._http = urllib3.PoolManager(retries=retry)

            if isinstance(auth, str):
                print("with token authentication.")
                self._http.headers["Authorization"] = f"Bearer {auth}"
            elif isinstance(auth, (list, tuple)):
                print("with basic authentication.")
                self._http.headers = urllib3.make_headers(basic_auth=":".join(auth))
            else:
                print("with no authentication.")

        self._http.headers["Content-Type"] = "application/json"

    def create(self,
               uri: str,
               data: dict,
               params: Union[Dict[Any, Any], None] = None
        ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Create request to the API, and returns the response
        """
        encoded_args = urlencode(params)
        url = self.host + uri + f"?{encoded_args}" if encoded_args else ""
        method = "POST"
        print(f"API Create Operation to {url}")

        if not isinstance(data, (str, bytes)):
            data = json.dumps(data)

        response = self._http.request(method,
                                      url,
                                      body=data,
                                      timeout=self.timeout)
        return self._proc_resp(method, response)

    def retrieve(self,
                 uri: str,
                 fields: Union[Dict[Any, Any], None] = None
        ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Retrieve request to the API, and returns the response
        """
        url = self.host + uri
        method = "GET"
        print(f"API Retrieve Operation to {url}")

        response =  self._http.request(method,
                                       url,
                                       fields=fields,
                                       timeout=self.timeout)
        return self._proc_resp(method, response)

    def update(
        self,
        uri: str,
        data: Union[Dict[Any, Any], str],
        params: Union[Dict[Any, Any], None] = None,
        with_patch: bool = False,
    ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Update request to the API, and returns the response
        """
        encoded_args = urlencode(params)
        url = self.host + uri + f"?{encoded_args}" if encoded_args else ""
        method = "PATCH" if with_patch else "PUT"
        print(f"API Update Operation to {url}")

        if isinstance(data, (str, bytes)):
            data = json.dumps(data)

        response = self._http.request(method,
                                      url,
                                      body=data,
                                      timeout=self.timeout)
        return self._proc_resp(method, response)

    def delete(self,
               uri: str,
               fields: Union[Dict[Any, Any], None] = None
        ) -> Union[Dict[Any, Any], bytes]:
        """
        Makes a basic Delete request to the API, and returns the response
        """
        url = self.host + uri
        method = "DELETE"
        print(f"API Delete Operation to {url}")

        response = self._http.request(method,
                                      self.host + uri,
                                      fields=fields,
                                      timeout=self.timeout)
        return self._proc_resp(method, response)

    def _proc_resp(self, method, response) -> Union[Dict[Any, Any], bytes]:
        """
        Processes the Responce from HTTP Requests in a standardize manner, and
        displays information.
        """
        print(
            f"  -> Method: {method}, Status Code: {response.status}, "
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
                print("  -> Server Error:", response.data.decode("utf-8"))
                msg = f"{error_type} Error with status code {response.status} returned"
                raise urllib3.exceptions.HTTPError(msg)

        try:
            return json.loads(response.data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return response.data
