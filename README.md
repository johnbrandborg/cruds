# CRUDs
[![Development](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml/badge.svg)](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml)
[![PyPI version](https://badge.fury.io/py/cruds.svg)](https://pypi.org/project/cruds/)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=johnbrandborg_cruds&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=johnbrandborg_cruds)

CRUDs is a simple high level library for Humans, inspired by [Python Requests](https://requests.readthedocs.io/en/latest/)
and written using [URLLib3 Team](https://github.com/urllib3).

```python
>>> import cruds
>>> catfact_ninja = cruds.Client(host="https://catfact.ninja/")
>>> data = catfact_ninja.read("fact")
>>> print(data)
```

Interact with RESTful APIs using Create, Read, Update and Delete requests quickly,
easily, and safely.

Features:
 * Authentication with a bearer token or username and password
 * Data serialization/deserialize (Only JSON format)
 * Request parameters as Dictionaries and automatically URL encoded
 * Default connection timeout (300 seconds)
 * Raises exceptions on bad status codes (Can be white listed)
 * Retries with back-off
 * SSL Verification
 * Logging for monitoring
 * JSON Schema Validation
 * Interfaces as Configuration

### Installation

To install a stable version use [PyPI](https://pypi.org/project/cruds/).

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

The library has been created with extensibility in mind.  There is two ways that
this can be done:

 1. Interface as Configuration
 2. Subclass the Client and add methods manually

**Interface as Configuration**

CRUDs supports creating interfaces with large amounts of models as configuration.
This significantly reduces the amount of python coding needed, and the common
methods can be reused.

Within the CRUDs package preconfigured Interfaces have been created.  They are:
 * Planhat - https://docs.planhat.com/

#### How to create and use a custom interfaces

Step 1 - Create the Interface configuration

```yaml
# catfactninja.yml
version: 1
api:
  - name: CatFactNinja
    docstring: |
        New API.  Generated using Interface as Configuration.
    package: catfactninja
    models:
     - name: fact
       methods:
        - get_multiple
       uri: fact
```

Step 2 - Create the methods as python code that will handle the interface logic

```python
""" catfactninja.py """
from cruds import Client

def __init__(self):
    """
    This is the Interfaces initialization magic method.
    """
    self.client = Client(host="http://catfact.ninja/")

def get_multiple(self, num=1):
    """
	Get multiple facts from the model as a generator.

    The owner is the Interface Class. The Model URI is also added automatically
    """

	while num > 0:
		yield self._owner.client.read(f"self._uri")
		num -= 1
```

Step 3 - Load the configuration and import the interface

```python
from cruds.interfaces import load_config

load_config("catfactninja.yml")
from cruds.interfaces import CatFactNinja

catfactninja = CatFactNinja()

# Class Instance now has 'interface.model.logic'
for fact in catfactninja.fact.get_multiple(3)
	print(fact)
```

**Subclass Client**

The approach is to create a new class and add the logic requirements needed to
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

## To Do List
- [ ] OAuth Client for Authentication
- [ ] Interfaces as Configuration
- [ ] Schema Validation

## License
CRUDs is released under the MIT License. See the bundled LICENSE file for details.

## Credits
* [URLLib3 Team](https://github.com/urllib3)
