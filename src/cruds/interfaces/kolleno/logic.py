from collections.abc import Generator
from pathlib import Path
from typing import Any, Final
from urllib.parse import quote

from cruds.core import Client, _FieldValue


KOLLENO_API_HOST: Final = "https://api.kolleno.com/v1"


def __init__(
    self,
    domain_name: str = KOLLENO_API_HOST,
    client_id: str | None = None,
    client_secret: str | None = None,
    **kwargs: Any,
) -> None:
    """Create a Kolleno client using credentials from an Open API key."""
    for name, value in {
        "domain_name": domain_name,
        "client_id": client_id,
        "client_secret": client_secret,
    }.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    if any(character in f"{client_id}{client_secret}" for character in "\r\n"):
        raise ValueError("Kolleno credentials cannot contain line breaks")

    self.client = Client(host=domain_name, **kwargs)
    self.client.request_headers["Authorization"] = f"API {client_id}:{client_secret}"


def _build_uri(self, *path: str) -> str:
    """Build a resource URI, escaping each dynamic path component."""
    components = [self._uri.strip("/")]
    for value in path:
        if value is None or not str(value).strip():
            raise ValueError("Kolleno path components cannot be empty")
        components.append(quote(str(value), safe=""))
    return "/".join(components) + "/"


def get_list(self, *path: str, **params: Any) -> dict[Any, Any] | bytes:
    """Retrieve one page of resources."""
    return self._owner.client.read(self._build_uri(*path), params=params or None)


def get_all(
    self,
    *path: str,
    limit: int = 100,
    offset: int = 0,
    **params: Any,
) -> Generator[dict[str, Any], None, None]:
    """Yield every result from a Kolleno offset-paginated endpoint."""
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")

    while True:
        response = self.get_list(*path, limit=limit, offset=offset, **params)
        if not isinstance(response, dict):
            raise TypeError("Expected a dictionary from a paginated Kolleno endpoint")

        results = response.get("results")
        if not isinstance(results, list):
            raise TypeError("Expected a results list from a paginated Kolleno endpoint")

        yield from results

        offset += len(results)
        count = response.get("count")
        if not results or response.get("next") is None:
            break
        if isinstance(count, int) and offset >= count:
            break


def get_by_id(
    self, *path: str, params: dict[Any, Any] | None = None
) -> dict[Any, Any] | bytes:
    """Retrieve a resource using its complete hierarchy of identifiers."""
    return self._owner.client.read(self._build_uri(*path), params=params)


def create(
    self,
    *path: str,
    data: dict[Any, Any],
    params: dict[Any, Any] | None = None,
    files: dict[str, _FieldValue] | None = None,
) -> dict[Any, Any] | bytes:
    """Create a resource below the supplied parent identifiers."""
    return self._owner.client.create(
        self._build_uri(*path),
        data=data,
        params=params,
        files=files,
    )


def update(
    self,
    *path: str,
    data: dict[Any, Any] | str,
    params: dict[Any, Any] | None = None,
    files: dict[str, _FieldValue] | None = None,
) -> dict[Any, Any] | bytes:
    """Partially update a resource using PATCH."""
    return self._owner.client.update(
        self._build_uri(*path),
        data=data,
        params=params,
        files=files,
    )


def delete(
    self, *path: str, params: dict[Any, Any] | None = None
) -> dict[Any, Any] | bytes:
    """Delete a resource using its complete hierarchy of identifiers."""
    return self._owner.client.delete(self._build_uri(*path), params=params)


def download(
    self,
    *resource_path: str,
    path: str | Path | None = None,
    filename: str | None = None,
    params: dict[Any, Any] | None = None,
) -> Path:
    """Download a PDF or report file to the local filesystem."""
    return self._owner.client.download(
        self._build_uri(*resource_path),
        path=path,
        filename=filename,
        params=params,
    )
