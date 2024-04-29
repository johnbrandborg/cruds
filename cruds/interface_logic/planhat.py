from datetime import datetime
from logging import getLogger
from time import sleep
from typing import Any, Dict, Generator, List, Union

from cruds.core import Client

logger = getLogger(__name__)


class PlanhatUpsertError(BaseException):
    pass


# Interface Methods

def __init__(self,
             company_id: str,
             tenant_token=None,
             calls_per_min=200,
             **kwargs) -> None:
    self.client = Client(host=f"https://api.planhat.com/", **kwargs)
    self.company_id = company_id
    self.tenant_token = tenant_token
    self.bulk_upsert_response = []
    self.calls_per_min = calls_per_min


@property
def calls_per_min(self) -> int:
    return self._calls_per_min


@calls_per_min.setter
def calls_per_min(self, value) -> None:
    self._calls_per_min = value
    self._delay = 60 / max(min(value, 200), 1)


def bulk_upsert_response_check(self) -> None:
    """
    Checks the response returned by Bulk Upserts, and raises an exception if one is found.
    """
    if not self.bulk_upsert_response:
        logger.info("Bulk Upsert response is empty.")
        return

    for results in self.bulk_upsert_response:
        for error in (
            {"type": key, "count": len(value)}
            for key, value in results.items()
            if "Errors" in key and isinstance(value, list)
        ):
            if error["count"]:
                raise PlanhatUpsertError(f"Errors found: {results[error['type']]}")

            logger.info(f"{error['type']} check passed.")


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

    company_params = {}

    if external_id:
        company_params["externalId"] = str(external_id)

    if source_id:
        company_params["sourceId"] = str(source_id)

    if status:
        if isinstance(status, (list, tuple)):
            company_params["status"] = ",".join(status)
        else:
            company_params["status"] = str(status)

    return self._owner.client.read(f"leancompanies", params=company_params)


def get_list(self,
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


def bulk(self, data: dict) -> dict:
    """
    To push dimension data into Planhat is is required to specify the Tenant Token (tenantUUID) in
    the request URL. This token is a simple uui identifier for your tenant and it can be found in
    the Developer module under the Tokens section.
    """
    return self._owner.analytics_client.update(f"{self._uri}/{self._owner.tenant_token}",
                                               data,
                                               with_post=True)


def bulk_upsert(self,
                data: Dict[Any, Any],
                step=5000,
                with_post=False,
                ) -> List[Dict[str, Union[int, List[str]]]]:
    """
    Takes data in form of JSON and updates entries already in PlanHat.
    (Limit of 5,000 items per request)

    To create an asset it's required define a name and a valid companyId.
    To update an asset it is required to specify in the payload one of the
    following keyables: _id, sourceId and/or externalId.
    """
    self._owner.bulk_upsert_response.clear()
    operation = self.create if with_post else self.update

    for reference in range(0, len(data), step):
        next_reference = reference + step
        self._owner.bulk_upsert_response.append(operation(self._uri, data[reference:next_reference]))
        logger.info(f"  -> Bulk Records Delivered: {reference} - {next_reference - 1}")
        sleep(self._owner._delay)

    return self._owner.bulk_upsert_response



@staticmethod
def epoc_days_format(date: str, reference="1970-01-01") -> int:
    """
    Takes an ISO formatted datetime string and returns the amount of lapsed
    that has lapsed.  Default reference is 1st January 1970.
    """
    return (datetime.fromisoformat(date) - datetime.fromisoformat(reference)).days


def get_dimension_data(
    self,
    from_day: str,
    to_day: str,
    company_id=None,
    dimension_id=None,
    limit=10000,
    max_requests=0,
) -> Generator:
    """
    A generator that retrieves all dimensiondata for a given time range.
    """
    limit = max(limit, 1)

    params: Dict[str, Any] = {
        "from": self.epoc_days_format(from_day),
        "to": self.epoc_days_format(to_day),
        "limit": limit,
        "offset": 0,
    }

    if company_id:
        params["cId"] = company_id

    if dimension_id:
        params["dimid"] = dimension_id

    yield from self._get_all_data(self._uri, params, max_requests)


def _get_all_data(self, uri, params, max_requests) -> Generator:
    """
    A generator that retrieves all model data for a given selection
    """
    retrieved = 0
    requests = 0

    while retrieved >= params["limit"] or requests == 0:
        data = self._owner.client.read(uri, params)
        retrieved = len(data)
        requests += 1

        logger.info(f"  -> Records Retrieved: {params['offset'] + retrieved}")

        yield data

        if requests >= max_requests and max_requests != 0:
            logger.info("Max requests reached.")
            return

        params["offset"] += retrieved
        sleep(self._owner._delay)

    logger.info("Completed getting all data.")


## User Activity - Analytics Endpoint

def create_activity(self, data: dict) -> Union[Dict[Any, Any], bytes]:
    """
    Creates user activity.  Required data keys are email or externalId.
    Ensure you create the PlanHat instance with analytics set to True.

    To use this method you don't need an API auth token.  Just supply the
    tenant_token instead.
    """

    if self._owner.tenant_token and not hasattr(self, "analytics_client"):
        self.analytics_client = Client(host=f"https://analytics.planhat.com/")

    return self.analytics_client.create(f"{self._uri}/{self._owner.tenant_token}", data)


def segment(self, data: dict) -> Union[Dict[Any, Any], bytes]:
    """
    Segment can be used to send User Events (user tracking data) to Planhat.
    Required data keys are type, and trait.  trait is an object.

    To use this method you must use the tenant token as the auth parameter
    for the instance creation.
    """

    if self._owner.tenant_token and not hasattr(self, "segment_client"):
        self.segment_client = Client(host=f"https://analytics.planhat.com/",
                                     auth=(self._owner.tenant_token,""))

    return self.segment_client.create("dock/segment", data)
