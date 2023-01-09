# Python RESTful Client 2
[![Python appliction](https://github.com/johnbrandborg/restful-client2/workflows/Python%20application/badge.svg)](https://github.com/johnbrandborg/restful-client2/actions?query=workflow%3A%22Python+application%22)
[![PyPI version](https://badge.fury.io/py/RESTful-Client.svg)](https://pypi.org/project/RESTful-Client2/)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=johnbrandborg_restful-client&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=johnbrandborg_restful-client)

RESTful Clients2 is a simple API library for Humans, inspired by [Python Requests](https://requests.readthedocs.io/en/latest/)

```python
>>> import restful_client2
>>> cf = restful_client2.CRUD(host="https://catfact.ninja/")
>>> data = cf.read("fact")
```

Focus on using Python data types instead of worrying about serialisation.
Authentication, Timeouts, Retries, Backoff are all built in and can be adjusted.

### Installation

You can install the client using PIP like so.

```bash
pip install RESTful-Client2
```

### Logging

If you want to see logging set the level using the standard logging interface.
This logging is also possible with URLLib3 for debugging low level issues.

``` python
>>> import logging
>>> import restful_client2
>>> restful_client2.add_stderr_logger(logging.DEBUG)
```

### Extending

The library has been created with extensability in mind.  You can Sub Class CRUD
for example and add the logic requirements needed to make the requests.

```python
from restful_client2 import CRUD

class CatFactNinja(CRUD):
    """Cat Fact Ninja Interface"""

    _fact_uri = "fact"

    def __init__(self, **kwargs):
        host = "http://catfact.ninja/"
        super().__init__(host=host, **kwargs)

    def fact(self):
        """ Get a Fact about Cats"""
        return self.read(self._fact_uri)

cat = CatFactNinja()
print(cat.fact())
```

## Todo List
- [ ] OAuth Client for Authentication

## License
RESTful-Client is released under the MIT License. See the bundled LICENSE file for details.

## Credits
* [URLLib3 Team](https://github.com/urllib3)
