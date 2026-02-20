# CRUDs

[![PyPI - Version](https://img.shields.io/pypi/v/cruds)](https://pypi.org/project/cruds/)
[![Supported Python Version](https://img.shields.io/pypi/pyversions/cruds?logo=python&logoColor=FFE873)](https://pypi.org/project/cruds/)
[![Development](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml/badge.svg)](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=johnbrandborg_cruds&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=johnbrandborg_cruds)
[![Documentation Status](https://readthedocs.org/projects/cruds/badge/?version=latest)](https://cruds.readthedocs.io/en/latest/?badge=latest)

**CRUDs** is a lightweight Python client for REST APIs — create, read, update,
and delete with zero boilerplate.

```python
import cruds

api = cruds.Client("https://api.example.com", auth="your-token")

# Create a resource
user = api.create("users", data={"name": "Ada", "role": "engineer"})

# Read it back
user = api.read(f"users/{user['id']}")

# Update it
api.update(f"users/{user['id']}", data={"role": "lead"})

# Delete it
api.delete(f"users/{user['id']}")
```

No response objects to unpack. No manual JSON parsing. No boilerplate retry
logic. Just your data.

## Quickstart

```bash
pip install cruds
```

```python
import cruds

catfacts = cruds.Client("catfact.ninja")
fact = catfacts.read("fact")
print(fact["fact"])
```

## Why CRUDs over requests/httpx?

| You get                    | Without writing          |
|----------------------------|--------------------------|
| Semantic CRUD methods      | HTTP method boilerplate  |
| Automatic JSON SerDes      | `.json()` / `.raise_for_status()` calls |
| Retry with backoff         | `HTTPAdapter` / `Retry` setup |
| Bearer, Basic & OAuth2 auth| Manual header management |
| SSL verification           | `certifi` wiring         |

```python
# requests — 6 lines of ceremony
import requests
response = requests.get("https://api.example.com/users",
                        headers={"Authorization": "Bearer token"})
response.raise_for_status()
users = response.json()

# CRUDs — 2 lines of intent
import cruds
users = cruds.Client("api.example.com", auth="token").read("users")
```

## Features

- **Authentication** — Bearer tokens, username/password, and OAuth2 (Client
  Credentials, Resource Owner Password, Authorization Code with CSRF protection)
- **JSON Serialization** — Send and receive Python dicts and lists directly
- **Retries with backoff** — Configurable retry count, backoff factor, and
  status codes (429, 500–504, etc.)
- **Error handling** — Automatic exceptions for 4xx/5xx responses
- **SSL verification** — Enabled by default via certifi
- **Logging** — Built-in INFO/DEBUG logging for monitoring
- **Interfaces** — Build SDKs with YAML configuration (ships with a full
  [Planhat](https://cruds.readthedocs.io/en/latest/interfaces.html#planhat)
  interface)

## Documentation

Full user guide, API reference, and examples at
**[cruds.readthedocs.io](https://cruds.readthedocs.io)**.

## License

MIT — see [LICENSE](https://github.com/johnbrandborg/cruds/blob/main/LICENSE).

## Credits

* [urllib3 Team](https://github.com/urllib3)
