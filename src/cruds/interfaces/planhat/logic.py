from copy import deepcopy
from datetime import datetime
from logging import getLogger
from time import sleep
from typing import Any, Dict, Generator, List, Union

from cruds.core import Client
from .exception import PlanhatUpsertError


logger = getLogger(__name__)

PLANHAT_API_HOST = "https://api.planhat.com/"
PLANHAT_ANALYTICS_HOST = "https://analytics.planhat.com/"


# Interface Methods


def __init__(
    self, api_token: str, tenant_token=None, calls_per_min=200, **kwargs
) -> None:
    self.client = Client(host=PLANHAT_API_HOST, auth=api_token, **kwargs)
    self.tenant_token = tenant_token
    self.calls_per_min = calls_per_min
    self._bulk_upsert_response = {}


@property
def calls_per_min(self) -> int:
    return self._calls_per_min


@calls_per_min.setter
def calls_per_min(self, value) -> None:
    self._calls_per_min = value
    self._delay = 60 / max(min(value, 200), 1)


@staticmethod
def epoc_days_format(date: str, reference="1970-01-01") -> int:
    """
    Takes an ISO formatted datetime string and returns the amount of lapsed
    that has lapsed.  Default reference is 1st January 1970.
    """
    return (datetime.fromisoformat(date) - datetime.fromisoformat(reference)).days


@property
def tenant_token(self) -> str:
    if self.__tenant_token is None:
        raise RuntimeError("No tenant token has been supplied")

    return self.__tenant_token


@tenant_token.setter
def tenant_token(self, value) -> None:
    self.__tenant_token = value

    if value is not None:
        self.client_analytics = Client(host=PLANHAT_ANALYTICS_HOST, auth=(value, ""))


def bulk_upsert_response_check(self) -> None:
    """
    Checks the response returned by Bulk Upserts, and raises an exception if one is found.
    """
    if not self._bulk_upsert_response:
        logger.info("Bulk Upsert response is empty.")
        return

    for error in (
        {"type": key, "count": len(value)}
        for key, value in self._bulk_upsert_response.items()
        if "Errors" in key and isinstance(value, list)
    ):
        if error["count"]:
            raise PlanhatUpsertError(
                f"Errors found: {self._bulk_upsert_response[error['type']]}"
            )

        logger.info(f"{error['type']} check passed.")


def _sum_bulk_upsert_responses(self, total: dict, response: dict) -> None:
    """
    Takes two Dictionaries and sums or extends the values in the response into the
    total using common keys.  Only the first level is processed.
    """
    for key in response:
        if key in total and isinstance(response[key], (tuple, list, int, float)):
            total[key] = total[key] + response[key]
        else:
            total[key] = response[key]


# Model Methods


def model_init(self, owner, uri) -> None:
    self._owner = owner
    self._uri = uri


def create(self, data: dict) -> dict:
    """
    To create an entry it's required define a name and a valid companyId.

    You can instead reference the company externalId or sourceId using the following
    command structure: "companyId": "extid-[company externalId]" or "companyId":
    "srcid-[company sourceId]".
    """
    return self._owner.client.create(self._uri, data)


def bulk_upsert(
    self,
    data: Dict[Any, Any],
    chunk_size=5000,
) -> Dict[str, Union[int, List[str]]]:
    """
    Takes data in form of JSON and updates entries already in PlanHat.
    (Limit of 5,000 items per request)

    To create an asset it's required define a name and a valid companyId.
    To update an asset it is required to specify in the payload one of the
    following keyables: _id, sourceId and/or externalId.
    """
    self._bulk_upsert_response = {}

    for reference in range(0, len(data), chunk_size):
        next_reference: int = reference + chunk_size
        self._sum_bulk_upsert_responses(
            self._bulk_upsert_response,
            self._owner.client.update(
                self._uri,
                data[reference:next_reference],
                replace=True,
            ),
        )
        logger.info(f"  -> Bulk Records Delivered: {reference} - {next_reference - 1}")
        sleep(self._owner._delay)

    return self._bulk_upsert_response


def delete(self, identification: str) -> dict:
    """
    Deletes an entry in PlanHat by PlanID
    """
    return self._owner.client.delete(f"{self._uri}/{identification}")


def update(self, identification: str, data: dict) -> dict:
    """
    Updates an entry by PlanID, ExternalID or SourceID by prepending the
    id with either extid- or srcid-.
    """
    return self._owner.client.update(f"{self._uri}/{identification}", data)


def get_by_id(self, identification) -> dict:
    """
    Retrieves data by PlanID, ExternalID or SourceID by prepending the
    id with either extid- or srcid-.
    """
    return self._owner.client.read(f"{self._uri}/{identification}")


def get_lean_list(self, external_id=None, source_id=None, status=None) -> List[dict]:
    """
    When you need a lightweight list of all companies in Planhat to match against
    your own ids etc.

    For each company profile in Planhat you'll get back the Planhat Id,
    External Id, Source ID (eg Salesforce) as well as the name.
    When fetching lean companies there are some options that can be used via query
    params:

    externalId: Compay externalId.
    sourceId: Company sourceId.
    status: Company status, e.g. "lost", "prospect".
    """

    company_params: dict[str, Any] = {}

    if external_id:
        company_params["externalId"] = str(external_id)

    if source_id:
        company_params["sourceId"] = str(source_id)

    if status:
        if isinstance(status, (list, tuple)):
            company_params["status"] = status
        else:
            company_params["status"] = [item.strip() for item in status.split(",")]

    return self._owner.client.read("leancompanies", params=company_params)


def get_dimension_data(
    self,
    from_day: Union[int, str],
    to_day: Union[int, str],
    company_id=None,
    dimension_id=None,
    limit=10000,
    max_requests=0,
) -> Generator:
    """
    When fetching dimension data there are some options that can be used via query params:

    company_id: Id of company.
    dimension_id: Id of the dimension data.
    from_day: Epoc days integer or ISO formatted date string.
    to: Epoc days integer or ISO formatted date string.
    limit: Limit the list length.
    max_requests: maximum number of requests to make.
    """
    limit = max(limit, 1)

    params: Dict[str, Any] = {
        "from": self.epoc_days_format(from_day)
        if isinstance(from_day, str)
        else from_day,
        "to": self.epoc_days_format(to_day) if isinstance(to_day, str) else to_day,
        "limit": limit,
        "offset": 0,
    }

    if company_id:
        params["cId"] = company_id

    if dimension_id:
        params["dimid"] = dimension_id

    yield from self._get_all_data(self._uri, params, max_requests)


def get_list(
    self,
    sort: str = "-_id",
    select: str = "name, companyId",
    limit: int = 2000,
    max_requests: int = 0,
) -> Generator:
    """
    Creates a generator that retrieves yields the data as Dictionaries
    Select can be an empty string, but defaults to those fields needed for creation.
    """
    params: Dict[str, Union[str, int]] = {
        "sort": sort,
        "select": select,
        "limit": max(limit, 1),
        "offset": 0,
    }

    yield from self._get_all_data(self._uri, params, max_requests)


def _get_all_data(self, uri, params, max_requests) -> Generator:
    """
    A generator that retrieves all model data for a given selection
    """
    updated_params = deepcopy(params)

    retrieved: int = 0
    requests: int = 0

    # If we retrive less than the limit the API is indicating it has no more
    # data left to give.  Also requests set to 0 will loop for ever.
    while retrieved >= updated_params["limit"] or requests == 0:
        data: dict = self._owner.client.read(uri, updated_params)
        retrieved: int = len(data)
        requests += 1

        logger.info(f"  -> Records Retrieved: {updated_params['offset'] + retrieved}")

        yield data

        if requests >= max_requests and max_requests != 0:
            logger.info("Max requests reached.")
            break

        updated_params["offset"] += retrieved
        sleep(self._owner._delay)

    logger.info("Completed getting all data.")


## User Activity - Analytics Endpoint


def bulk_insert_metrics(self, data: dict) -> dict:
    """
    To push dimension data into Planhat it is required to specify the Tenant Token (tenantUUID) in
    the request URL. This token is a simple uui identifier for your tenant and it can be found in
    the Developer module under the Tokens section.
    """
    return self._owner.client_analytics.create(
        f"{self._uri}/{self._owner.tenant_token}", data
    )


def create_activity(self, data: dict) -> Union[Dict[Any, Any], bytes]:
    """
    Creates user activity.  Required data keys are email or externalId.
    Ensure you create the PlanHat instance with analytics set to True.

    To use this method you don't need an API auth token.  Just supply the
    tenant_token instead.
    """
    return self._owner.client_analytics.create(
        f"{self._uri}/{self._owner.tenant_token}", data
    )


def segment(self, data: dict) -> Union[Dict[Any, Any], bytes]:
    """
    Segment can be used to send User Events (user tracking data) to Planhat.
    Required data keys are type, and trait.  trait is an object.

    To use this method you must use the tenant token as the auth parameter
    for the instance creation.
    """
    # Retrieve tenant_token even though not used, to ensure client is created.
    self._owner.tenant_token
    return self._owner.client_analytics.create("dock/segment", data)
