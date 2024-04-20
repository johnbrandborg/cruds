from collections.abc import Iterator
from datetime import datetime
from enum import Enum, unique
from logging import getLogger
from time import sleep
from typing import Any, Union

from cruds.core import Client

logger = getLogger(__name__)


# Interface Methods

@unique
class Endpoints(Enum):
    api = "https://api.planhat.com"
    analytics = "https://analytics.planhat.com"


def __init__(self, company_id: str, analytics=False, **kwargs):
    host = Endpoints.analytics.value if analytics else Endpoints.api.value
    self.client = Client(host=host, **kwargs)
    self.company_id = company_id
    self.delay = 0.3


# Model Methods

def model_init(self, owner, uri):
    self._owner = owner
    self._uri = uri


def create(self, tenant_token: str, data: dict):
    """
    Creates user activity.  Required data keys are email or externalId.
    Ensure you create the PlanHat instance with analytics set to True.

    To use this method you don't need an API auth token.  Just supply the
    tenant_token instead.
    """
    assert self.host.startswith(
        "https://analytics."
    ), "PlanHat Instance is not enabled with analytics. Recreate with analytics=True"
    return self._owner.client.create(f"{self._user_activity_uri}/{tenant_token}", data)


def delete(self, planid: str) -> dict:
    """
    Deletes an entry in PlanHat by PlanID
    """
    return self._owner.client.delete(f"{self._uri}/{planid}")


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


def get_lean_list(self, external_id=None, source_id=None, status=None) -> list[dict]:
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


def get_list(self, sort: str = "-_id", select: str = "name, companyId", max_requests: int = 0) -> Iterator[dict[Any, Any]]:
    """
    Creates a generator that retrieves yields the data as Dictionaries
    Select can be an empty string, but defaults to those fields needed for creation.
    """
    yield from self._get_all_data(
        self._uri,
        self.create_model_params(sort, select, 2000),
        max_requests,
    )


def segment(self, data: dict) -> dict:
    """
    Segment can be used to send User Events (user tracking data) to Planhat.
    Required data keys are type, and trait.  trait is an object.

    To use this method you must use the tenant token as the auth parameter
    for the instance creation.
    """
    assert self.host.startswith(
        "https://analytics."
    ), "PlanHat Instance is not enabled with analytics. Recreate with analytics=True"
    return self.create("dock/segment", data)


@staticmethod
def create_model_params(sort, select, limit) -> dict[str, Any]:
    """
    A generator that retrieves all model data for a given selection
    """
    return {
        "sort": sort,
        "select": select,
        "limit": max(limit, 1),
        "offset": 0,
    }


@staticmethod
def epoc_days_format(date: str, reference="1970-01-01") -> int:
    """
    Takes an ISO formatted datetime string and returns the amount of lapsed
    that has lapsed.  Default reference is 1st January 1970.
    """
    return (datetime.fromisoformat(date) - datetime.fromisoformat(reference)).days


def get_dimensiondata(
    self,
    from_day: str,
    to_day: str,
    company_id=None,
    dimension_id=None,
    limit=10000,
    max_requests=0,
) -> Iterator[dict[Any, Any]]:
    """
    A generator that retrieves all dimensiondata for a given time range.
    """
    limit = max(limit, 1)

    params: dict[str, Any] = {
        "from": self.epoc_days_format(from_day),
        "to": self.epoc_days_format(to_day),
        "limit": limit,
        "offset": 0,
    }

    if company_id:
        params["cId"] = company_id

    if dimension_id:
        params["dimid"] = dimension_id

    yield from self._get_all_data(self._dimension_uri, params, max_requests)


def bulk_upsert(self, data: dict[Any, Any]) -> list[dict[str, Union[int, list[str]]]]:
    """
    Takes data in form of JSON and updates entries already in PlanHat.
    (Limit of 5,000 items per request)

    To create an asset it's required define a name and a valid companyId.
    To update an asset it is required to specify in the payload one of the
    following keyables: _id, sourceId and/or externalId.
    """
    return self._bulk_upsert(self._assets_uri, data)


def _get_all_data(self, uri, params, max_requests) -> Iterator[dict[Any, Any]]:
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
        sleep(self._owner.delay)

    logger.info("Completed getting all data.")


def _bulk_upsert(self, uri: str, data: dict[Any, Any], step=5000, with_post=False) -> list[dict[str, Union[int, list[str]]]]:
    self.bulk_upsert_response.clear()
    operation = self.create if with_post else self.update

    for reference in range(0, len(data), step):
        next_reference = reference + step
        self.bulk_upsert_response.append(operation(uri, data[reference:next_reference]))
        logger.info(f"  -> Bulk Records Delivered: {reference} - {next_reference - 1}")
        sleep(self._owner.delay)

    return self.bulk_upsert_response


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
                raise Exception(f"Errors found: {results[error['type']]}")

            logger.info(f"{error['type']} check passed.")
