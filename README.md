# "Create, Read, Update, Delete"s

[![PyPI - Version](https://img.shields.io/pypi/v/cruds)](https://pypi.org/project/cruds/)
[![Supported Python Version](https://img.shields.io/pypi/pyversions/cruds?logo=python&logoColor=FFE873)](https://pypi.org/project/cruds/)
[![Development](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml/badge.svg)](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=johnbrandborg_cruds&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=johnbrandborg_cruds)
[![Documentation Status](https://readthedocs.org/projects/cruds/badge/?version=latest)](https://cruds.readthedocs.io/en/latest/?badge=latest)

**CRUDs** is a high level client library for APIs written in Python, and is ideal for back-end
communication, automated data processing, and interactive environments like Notebooks.

```python
>>> import cruds
>>>
>>> catfact_ninja = cruds.Client("https://catfact.ninja/")
>>>
>>> data = catfact_ninja.read("fact")
>>> type(date)  # Python built-in data types you can use instantly!
<class 'dict'>
```

Make Create, Read, Update and Delete operations quickly, easily, and safely. CRUDs
aims to handle the majority of the setup needed for production so you can focus
on moving data.

Features:
 * Authentication: Username & Password, Bearer Token or OAuth2
 * JSON Serialization/Deserialization
 * Request parameters and automatically URL encoded
 * Default connection timeout (5 minutes)
 * Raises exceptions on bad status codes
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

Whether you are an data engineer wanting to retrieve or load data, a developer
writing software for the back-of-the-front-end, or someone wanting to contribute
to the project, for more information about CRUDs please visit
[Read the Docs](https://cruds.readthedocs.io).

## License

CRUDs is released under the MIT License. See the bundled
[LICENSE file](https://github.com/johnbrandborg/cruds/blob/main/LICENSE)
for details.

## Credits

* [URLLib3 Team](https://github.com/urllib3)
