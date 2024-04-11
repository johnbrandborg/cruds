# CRUDs
[![Python appliction](https://github.com/johnbrandborg/cruds/workflows/Python%20application/badge.svg)](https://github.com/johnbrandborg/cruds/actions?query=workflow%3A%22Python+application%22)
[![PyPI version](https://badge.fury.io/py/cruds.svg)](https://pypi.org/project/cruds/)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=johnbrandborg_cruds&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=johnbrandborg_cruds)

CRUDs is a simple high level library for Humans, inspired by [Python Requests](https://requests.readthedocs.io/en/latest/)

```python
>>> import cruds
>>> catfact_ninja = cruds.Client(host="https://catfact.ninja/")
>>> data = catfact_ninja.read("fact")
```

Interact with RESTful API using Create, Read, Update and Delete requests.
Focus on using Python data types instead of worrying about serialization.
Authentication, timeouts, retries, and rate limit back-off are all built in
and can be adjusted.

### Installation

You can install the client using PIP like so.

```bash
pip install cruds
```

### Logging

If you want to see logging set the level using the standard logging interface.
DEBUG will show you URLLib3, but INFO will give you general information from
the cruds.

``` python
>>> import logging
>>> import cruds
>>> logging.basicConfig(level=logging.INFO)
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
cruds is released under the MIT License. See the bundled LICENSE file for details.

## Credits
* [URLLib3 Team](https://github.com/urllib3)
