from copy import deepcopy
from collections.abc import Generator
from datetime import datetime
from json import dumps
from logging import getLogger
from time import sleep
from typing import Any

from cruds.core import Client
from .exception import PlanhatUpsertError


logger = getLogger(__name__)

PLANHAT_API_HOST = "https://api.planhat.com/"
PLANHAT_ANALYTICS_HOST = "https://analytics.planhat.com/"
PLANHAT_BULK_LIMIT = 5000
PLANHAT_ANALYTICS_BODY_LIMIT = 32 * (1024**2)


class PlanhatClient(Client):
    """Client that preserves structured errors returned by Planhat bulk APIs."""

    def _process_resp(self, method, response) -> dict[Any, Any] | bytes:
        if (
            self.raise_status
            and response.status in {400, 403}
            and response.status not in self.status_ignore
        ):
            try:
                payload = response.json()
            except (ValueError, TypeError):
                payload = None

            if isinstance(payload, dict):
                errors = {
                    key: value
                    for key, value in payload.items()
                    if key.lower().endswith("errors")
                    and isinstance(value, list)
                    and value
                }
                if errors:
                    raise PlanhatUpsertError(errors)

        return super()._process_resp(method, response)


# Interface Methods


def __init__(
    self,
    api_token: str | None = None,
    tenant_token: str | None = None,
    calls_per_min: int | float = 200,
    **kwargs,
) -> None:
    self._client_kwargs = kwargs.copy()
    self.client = PlanhatClient(host=PLANHAT_API_HOST, auth=api_token, **kwargs)
    self.tenant_token = tenant_token
    self.calls_per_min = calls_per_min
    self._bulk_upsert_response: dict[str, Any] = {}


@property
def calls_per_min(self) -> int | float:
    return self._calls_per_min


@calls_per_min.setter
def calls_per_min(self, value: int | float) -> None:
    self._calls_per_min = max(min(value, 200), 1)
    self._delay = 60 / self._calls_per_min


@staticmethod
def epoch_days_format(date: str, reference: str = "1970-01-01") -> int:
    """
    Return the number of elapsed days from the reference ISO date.
    """
    return (datetime.fromisoformat(date) - datetime.fromisoformat(reference)).days


@property
def tenant_token(self) -> str:
    if self.__tenant_token is None:
        raise RuntimeError("No tenant token has been supplied")

    return self.__tenant_token


@tenant_token.setter
def tenant_token(self, value: str | None) -> None:
    self.__tenant_token = value

    if value is not None:
        self.client_analytics = PlanhatClient(
            host=PLANHAT_ANALYTICS_HOST,
            auth=(value, ""),
            **self._client_kwargs,
        )


def bulk_upsert_response_check(self, response: dict[str, Any] | None = None) -> None:
    """
    Raise an exception containing every error category in a bulk response.

    If response is omitted, the most recent bulk response for this Planhat
    instance is checked.
    """
    response = self._bulk_upsert_response if response is None else response

    if not response:
        logger.info("Bulk Upsert response is empty.")
        return

    errors = {
        key: value
        for key, value in response.items()
        if key.lower().endswith("errors") and isinstance(value, list) and value
    }
    if errors:
        raise PlanhatUpsertError(errors)

    logger.info("Bulk Upsert response check passed.")


@staticmethod
def _sum_bulk_upsert_responses(total: dict, response: dict | bytes) -> None:
    """
    Takes two Dictionaries and sums or extends the values in the response into the
    total using common keys.  Only the first level is processed.

    If response is bytes (non-JSON), it will be ignored as it cannot be merged.
    """
    # Skip processing if response is not a dictionary (e.g., bytes)
    if not isinstance(response, dict):
        logger.debug(f"Skipping non-dict response: {type(response)}")
        return

    for key, value in response.items():
        matching_sequences = isinstance(value, (tuple, list)) and isinstance(
            total.get(key), type(value)
        )
        matching_numbers = (
            not isinstance(value, bool)
            and not isinstance(total.get(key), bool)
            and isinstance(value, (int, float))
            and isinstance(total.get(key), (int, float))
        )
        if key in total and (matching_sequences or matching_numbers):
            total[key] = total[key] + value
        else:
            total[key] = value


# Model Methods


def model_init(self, owner, uri) -> None:
    self._owner = owner
    self._uri = uri


def create(self, data: Any) -> dict:
    """
    To create an entry it's required define a name and a valid companyId.

    You can instead reference the company externalId or sourceId using the following
    command structure: "companyId": "extid-[company externalId]" or "companyId":
    "srcid-[company sourceId]".
    """
    return self._owner.client.create(self._uri, data)


def duplicate(self, data: Any) -> dict:
    """
    Duplicate time entries by id. Payload must include ``ids`` (list of
    time-entry _id values). See Planhat Time Entry API duplicate operation.
    """
    return self._owner.client.create(f"{self._uri}/duplicate", data)


def bulk_upsert(
    self,
    data: list[dict[str, Any]],
    chunk_size: int = PLANHAT_BULK_LIMIT,
    raise_on_error: bool = False,
) -> dict[str, Any]:
    """
    Takes data in form of JSON and updates entries already in PlanHat.
    (Limit of 5,000 items per request)

    To create an asset it's required define a name and a valid companyId.
    To update an asset it is required to specify in the payload one of the
    following keyables: _id, sourceId and/or externalId.
    """
    if not isinstance(chunk_size, int):
        raise TypeError("chunk_size must be an integer")
    if chunk_size < 1 or chunk_size > PLANHAT_BULK_LIMIT:
        raise ValueError(f"chunk_size must be between 1 and {PLANHAT_BULK_LIMIT}")

    response: dict[str, Any] = {}

    for reference in range(0, len(data), chunk_size):
        next_reference: int = reference + chunk_size
        self._owner._sum_bulk_upsert_responses(
            response,
            self._owner.client.update(
                self._uri,
                data[reference:next_reference],
                replace=True,
            ),
        )
        logger.info(f"  -> Bulk Records Delivered: {reference} - {next_reference - 1}")
        if next_reference < len(data):
            sleep(self._owner._delay)

    self._owner._bulk_upsert_response = response
    if raise_on_error:
        self._owner.bulk_upsert_response_check(response)

    return response


def delete(self, identification: str) -> dict:
    """
    Deletes an entry in PlanHat by PlanID
    """
    return self._owner.client.delete(f"{self._uri}/{identification}")


def update(self, identification: str, data: Any) -> dict:
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

    company_params: dict[str, Any] = {}

    if external_id:
        company_params["externalId"] = str(external_id)

    if source_id:
        company_params["sourceId"] = str(source_id)

    if status:
        if isinstance(status, (list, tuple)):
            company_params["status"] = ",".join(str(item).strip() for item in status)
        else:
            company_params["status"] = ",".join(
                item.strip() for item in status.split(",")
            )

    return self._owner.client.read("leancompanies", params=company_params)


def get_dimension_data(
    self,
    from_day: int | str,
    to_day: int | str,
    company_id=None,
    dimension_id=None,
    limit=10000,
    max_requests=0,
) -> Generator[list[dict[str, Any]], None, None]:
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

    params: dict[str, Any] = {
        "from": self.epoch_days_format(from_day)
        if isinstance(from_day, str)
        else from_day,
        "to": self.epoch_days_format(to_day) if isinstance(to_day, str) else to_day,
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
    select: str | None = "name, companyId",
    limit: int = 2000,
    max_requests: int = 0,
    **filters: Any,
) -> Generator[list[dict[str, Any]], None, None]:
    """
    Yield pages of model records, with optional selection and model filters.
    """
    params: dict[str, Any] = {
        "sort": sort,
        "limit": max(limit, 1),
        "offset": 0,
        **filters,
    }
    if select is not None:
        params["select"] = select

    yield from self._get_all_data(self._uri, params, max_requests)


def _get_all_data(
    self, uri: str, params: dict[str, Any], max_requests: int
) -> Generator[list[dict[str, Any]], None, None]:
    """
    A generator that retrieves all model data for a given selection
    """
    updated_params = deepcopy(params)

    requests: int = 0

    while max_requests == 0 or requests < max_requests:
        data = self._owner.client.read(uri, updated_params)
        if not isinstance(data, list):
            raise TypeError(
                f"Expected a list response while paginating {uri}, "
                f"received {type(data).__name__}"
            )

        retrieved = len(data)
        requests += 1

        logger.info(f"  -> Records Retrieved: {updated_params['offset'] + retrieved}")

        yield data

        if not data:
            break

        if retrieved < updated_params["limit"]:
            break

        if max_requests and requests >= max_requests:
            logger.info("Max requests reached.")
            break

        updated_params["offset"] += retrieved
        sleep(self._owner._delay)

    logger.info("Completed getting all data.")


## User Activity - Analytics Endpoint


def bulk_insert_metrics(
    self, data: Any, auto_chunk: bool = True, raise_on_error: bool = False
) -> dict[Any, Any] | bytes:
    """
    To push dimension data into Planhat it is required to specify the Tenant Token
    (tenantUUID) in the request URL. This token is a simple uui identifier for your
    tenant and it can be found in the Developer module under the Tokens section.
    """
    if auto_chunk is True and isinstance(data, list) and len(data) > 0:
        response: dict[str, Any] = {}
        chunk_size: int = calculate_metric_chunk_size(data)

        for reference in range(0, len(data), chunk_size):
            next_reference: int = reference + chunk_size
            self._owner._sum_bulk_upsert_responses(
                response,
                self._owner.client_analytics.create(
                    f"{self._uri}/{self._owner.tenant_token}",
                    data[reference:next_reference],
                ),
            )
            logger.info(
                f"  -> Bulk Metrics Delivered: {reference} - {next_reference - 1}"
            )

        self._owner._bulk_upsert_response = response
        if raise_on_error:
            self._owner.bulk_upsert_response_check(response)

        return response

    return self._owner.client_analytics.create(
        f"{self._uri}/{self._owner.tenant_token}", data
    )


def calculate_metric_chunk_size(
    data: list | dict,
    sample_per: int = 1000,
    max_bytes: int = PLANHAT_ANALYTICS_BODY_LIMIT,
    reduction: int = 10,
) -> int:
    """
    Determine a conservative, deterministic chunk size below the body limit.

    ``sample_per`` remains accepted for backward compatibility. Every row is
    measured so an unusually large unsampled row cannot exceed Planhat's limit.
    """
    logger.info("Calculating chunk size of metric data")

    if not isinstance(data, list):
        return 1
    if not data:
        return 0
    if max_bytes < 1:
        raise ValueError("max_bytes must be greater than zero")
    if reduction < 0 or reduction >= 100:
        raise ValueError("reduction must be between 0 and 99")

    effective_limit = int(max_bytes * (1 - reduction / 100)) - 2
    largest_item = max(len(dumps(item).encode()) + 1 for item in data)
    if largest_item > effective_limit:
        raise ValueError("A single analytics item exceeds the request body limit")

    chunk_size = max(effective_limit // largest_item, 1)
    logger.info(
        "Largest item: %d bytes, Size: %d rows, Bytes (%d%% Reduction)",
        largest_item,
        chunk_size,
        reduction,
    )

    return chunk_size


def create_activity(
    self,
    data: Any,
    bulk: bool = False,
    auto_chunk: bool = True,
    raise_on_error: bool = False,
) -> dict[Any, Any] | bytes:
    """
    Creates user activity.  Required data keys are email or externalId.
    Ensure you create the PlanHat instance with analytics set to True.

    To use this method you don't need an API auth token.  Just supply the
    tenant_token instead.

        Parameters:
                data (dict|list): Data to be serialed and deliveryed
                bulk (bool): Use the bulk request rather than realtime
                auto_chunk (bool): Automatically chunk data to avoid 32MB limit

        Returns:
                data (dict|bytes): Deserialed or byte data
    """
    bulk_path: str = "/bulk" if bulk is True else ""

    # Only apply auto-chunking for bulk operations with list data
    if bulk and auto_chunk and isinstance(data, list) and len(data) > 0:
        response: dict[str, Any] = {}
        chunk_size: int = calculate_metric_chunk_size(data)

        for reference in range(0, len(data), chunk_size):
            next_reference: int = reference + chunk_size
            self._owner._sum_bulk_upsert_responses(
                response,
                self._owner.client_analytics.create(
                    f"{self._uri}{bulk_path}/{self._owner.tenant_token}",
                    data[reference:next_reference],
                ),
            )
            logger.info(
                f"  -> Bulk Activity Delivered: {reference} - {next_reference - 1}"
            )

        self._owner._bulk_upsert_response = response
        if raise_on_error:
            self._owner.bulk_upsert_response_check(response)

        return response

    return self._owner.client_analytics.create(
        f"{self._uri}{bulk_path}/{self._owner.tenant_token}", data
    )


def segment(
    self, data: Any, auto_chunk: bool = True, raise_on_error: bool = False
) -> dict[Any, Any] | bytes:
    """
    Segment can be used to send User Events (user tracking data) to Planhat.
    Required data keys are type, and trait.  trait is an object.

    To use this method you must use the tenant token as the auth parameter
    for the instance creation.

        Parameters:
                data (dict|list): Data to be serialized and delivered
                auto_chunk (bool): Automatically chunk data to avoid 32MB limit

        Returns:
                data (dict|bytes): Deserialized or byte data
    """
    # Retrieve tenant_token even though not used, to ensure client is created.
    self._owner.tenant_token

    # Apply auto-chunking for list data
    if auto_chunk and isinstance(data, list) and len(data) > 0:
        response: dict[str, Any] = {}
        chunk_size: int = calculate_metric_chunk_size(data)

        for reference in range(0, len(data), chunk_size):
            next_reference: int = reference + chunk_size
            self._owner._sum_bulk_upsert_responses(
                response,
                self._owner.client_analytics.create(
                    "dock/segment",
                    data[reference:next_reference],
                ),
            )
            logger.info(
                f"  -> Bulk Segment Delivered: {reference} - {next_reference - 1}"
            )

        self._owner._bulk_upsert_response = response
        if raise_on_error:
            self._owner.bulk_upsert_response_check(response)

        return response

    return self._owner.client_analytics.create("dock/segment", data)
