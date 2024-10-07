# "Create, Read, Update, Delete"s

[![PyPI - Version](https://img.shields.io/pypi/v/cruds)](https://pypi.org/project/cruds/)
[![Supported Python Version](https://img.shields.io/pypi/pyversions/cruds?logo=python&logoColor=FFE873)](https://pypi.org/project/cruds/)
[![Development](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml/badge.svg)](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=johnbrandborg_cruds&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=johnbrandborg_cruds)
[![Documentation Status](https://readthedocs.org/projects/cruds/badge/?version=latest)](https://cruds.readthedocs.io/en/latest/?badge=latest)

CRUDs is a high level library for API's, and is ideal for automated data processing
and interactive environments like Notebooks.

```python
>>> import cruds
>>>
>>> catfact_ninja = cruds.Client(host="https://catfact.ninja/")
>>>
>>> data = catfact_ninja.read("fact")
>>> type(date)
<class 'dict'>
```

Make Create, Read, Update and Delete operations quickly, easily, and safely. CRUDs
aims to handle the majority of the setup needed for production so you can focus
on moving data.

Features:
 * Authentication with a bearer token, username & password, or OAuth2 (Beta)
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
$ pip install cruds
```

### Documentation

For more information about how to use CRUDS, please visit [Read the Docs](https://cruds.readthedocs.io).

## License

CRUDs is released under the MIT License. See the bundled LICENSE file for details.

## Credits

* [URLLib3 Team](https://github.com/urllib3)
