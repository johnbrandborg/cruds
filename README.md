# CRUDs
[![Development](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml/badge.svg)](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml)
[![PyPI version](https://badge.fury.io/py/cruds.svg)](https://pypi.org/project/cruds/)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=johnbrandborg_cruds&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=johnbrandborg_cruds)

CRUDs is a simple high level library for Humans, inspired by [Python Requests](https://requests.readthedocs.io/en/latest/)
and written using URLLib3.

```python
>>> import cruds
>>> catfact_ninja = cruds.Client(host="https://catfact.ninja/")
>>> data = catfact_ninja.read("fact")
```

Interact with RESTful APIs using Create, Read, Update and Delete requests quickly,
easily, and safely.

Features:
 * Authentication with a bearer token or username and password
 * Data serialization/deserialize (Only JSON format)
 * Request parameters as Dictionaries and automatically URL encoded
 * Default connection timeout (300 seconds)
 * Raises exceptions on bad status codes (Can be whitelisted)
 * Retries with back-off
 * SSL Verification
 * Logging for monitoring

### Installation

You can install the client using PIP like so.

```bash
pip install cruds
```

### Usage

All features can be adjusted on the Client to suit most needs.

```python
from cruds import Client

# Authentication with Username and Password
api = Client(host="https://localhost/api/v1/",
             auth=("username", "password"))

# Authentication with Token
api = Client(host="https://localhost/api/v1/",
             auth="bearer-token")

# Send and receive raw data and ignore bad status codes
api = Client(host="https://localhost/api/v1/",
             serialize=False,
             raise_status=False)

# Disable SSL Verification
api = Client(host="https://localhost/api/v1/",
             verify_ssl=False)
```

### Logging

If you want to see logging set the level using the standard logging interface.
DEBUG will show you URLLib3, but INFO will give you general information from
the CRUDs Client.

``` python
import logging
import cruds
logging.basicConfig(level=logging.INFO)
```

### Extensibility

The library has been created with extensibility in mind.  You can Sub Class Client
for example and add the logic requirements needed to make the requests.

```python
from cruds import Client

class CatFactNinja(Client):
    """Cat Fact Ninja Interface"""

    _fact_uri = "fact"

    def __init__(self, **kwargs):
        host = "http://catfact.ninja/"
        super().__init__(host=host, **kwargs)

    @property
    def fact(self):
        """ Get a Fact about Cats"""
        return self.read(self._fact_uri)

cat = CatFactNinja()
print(cat.fact)
```

## Todo List
- [ ] OAuth Client for Authentication

## License
CRUDs is released under the MIT License. See the bundled LICENSE file for details.

## Credits
* [URLLib3 Team](https://github.com/urllib3)
