# Python RESTful Client 2
[![Python appliction](https://github.com/johnbrandborg/restful-client/workflows/Python%20application/badge.svg)](https://github.com/johnbrandborg/restful-client/actions?query=workflow%3A%22Python+application%22)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=johnbrandborg_restful-client&metric=alert_status)](https://sonarcloud.io/dashboard?id=johnbrandborg_restful-client)
[![PyPI version](https://badge.fury.io/py/RESTful-Client.svg)](https://pypi.org/project/RESTful-Client/)

RESTful is a simple API library for Humans, inspired by [Python Requests](https://requests.readthedocs.io/en/latest/)

```python
>>> import restful_client2
>>> cf = restful_client2.CRUD(host="https://catfact.ninja/")
>>> data = cf.retrieve("fact")
```

### Installation

You can install the client using PIP like so.

```bash
pip install RESTful-Client2
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

    @property
    def fact(self):
        """ Get a Fact about Cats"""
        return self.retrieve(self._fact_uri).get("fact", "")

cat = CatFactNinja()
print(cat.fact)
```

## Todo List
- [ ] OAuth Client for Authentication

## License
RESTful-Client is released under the MIT License. See the bundled LICENSE file for details.

## Credits
* [URLLib3 Team](https://github.com/urllib3)
