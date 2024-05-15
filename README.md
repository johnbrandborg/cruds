# CRUDs

[![PyPI - Version](https://img.shields.io/pypi/v/cruds)](https://pypi.org/project/cruds/)
[![Supported Python Version](https://img.shields.io/pypi/pyversions/cruds?logo=python&logoColor=FFE873)](https://pypi.org/project/cruds/)
[![PyPI downloads](https://img.shields.io/pypi/dm/cruds)](https://pypistats.org/packages/cruds)
[![Development](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml/badge.svg)](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=johnbrandborg_cruds&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=johnbrandborg_cruds)

CRUDs is a high level library for API's, and is ideal for automation system and/or
interactive environments like Notebooks.

```python
>>> import cruds
>>> catfact_ninja = cruds.Client(host="https://catfact.ninja/")
>>> data = catfact_ninja.read("fact")
>>> print(data)
```

Make Create, Read, Update and Delete requests quickly, easily, and safely.  CRUDs
aims to handle the majority of the general setup so you can focus on moving data.

Features:
 * Authentication with a bearer token or username and password
 * Data serialization/deserialize (Only JSON format)
 * Request parameters as Dictionaries and automatically URL encoded
 * Default connection timeout (300 seconds)
 * Raises exceptions on bad status codes (Can be white listed)
 * Retries with back-off
 * SSL Verification
 * Logging for monitoring
 * Interfaces (SDK Creation)

### Installation

To install a stable version use [PyPI](https://pypi.org/project/cruds/).

```bash
pip install cruds
```

### General Usage

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

### Interfaces

Within CRUDs pre-configured Interfaces have been created.  To use an Interface
import them from interface packages under `cruds.interfaces.<name>`.

Currently available:
* Planhat - https://docs.planhat.com/

Example:
```python
from cruds.interfaces.planhat import Planhat

planhat = Planhat(api_token="9PhAfMO3WllHUmmhJA4eO3tJPhDck1aKLvQ5osvNUfKYdJ7H")

help(planhat)
```

### Logging

Because CRUDs is high level it has verbose logging to assist with capturing
information around general operations.

If you want to see logging set the level using the standard logging interface.
DEBUG will show you URLLib3, but INFO will give you general information from
the CRUDs Client.

``` python
import logging
import cruds

logging.basicConfig(level=logging.INFO)
```

### Extensibility

The library has been created with extensibility in mind, so that Software Development
Kits can be created.  There is two ways that this can be done, one as described below
or by creating an Interface.

The basic approach is to create a new class and add the logic requirements needed to
make the requests.

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

CRUDs supports creating interfaces with large amounts of models as a mixture of
YAML configuration and functions for the common logic.  This significantly
reduces the amount of python coding needed, and the common methods can be reused.

## To Do List

- [ ] OAuth Client for Authentication
- [X] Interfaces as Configuration

## License

CRUDs is released under the MIT License. See the bundled LICENSE file for details.

## Credits

* [URLLib3 Team](https://github.com/urllib3)
