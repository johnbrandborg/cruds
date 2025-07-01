# "Create, Read, Update, Delete"s

[![PyPI - Version](https://img.shields.io/pypi/v/cruds)](https://pypi.org/project/cruds/)
[![Supported Python Version](https://img.shields.io/pypi/pyversions/cruds?logo=python&logoColor=FFE873)](https://pypi.org/project/cruds/)
[![Development](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml/badge.svg)](https://github.com/johnbrandborg/cruds/actions/workflows/development.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=johnbrandborg_cruds&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=johnbrandborg_cruds)
[![Documentation Status](https://readthedocs.org/projects/cruds/badge/?version=latest)](https://cruds.readthedocs.io/en/latest/?badge=latest)

**CRUDs** is a high level client library for APIs written in Python, and is ideal for back-end
communication, automated data processing and interactive environments like Notebooks.

```python
>>> import cruds
>>>
>>> catfact_ninja = cruds.Client("catfact.ninja")
>>>
>>> data = catfact_ninja.read("fact")
>>> type(date)  # Python built-in data types you can use instantly!
<class 'dict'>
```

## Why CRUDs?

When working with APIs, you have several options. Here's why CRUDs might be the right choice:

**vs. requests/httpx/urllib3:**
- **Semantic API Design**: Think about what you're doing (create, read, update, delete) instead of HTTP methods
- **Production-Ready**: Built-in retry logic, error handling, and logging without configuration
- **Simplified Auth**: OAuth2, bearer tokens, and basic auth handled automatically
- **Data-First**: Returns Python data structures directly instead of response objects

**vs. SDKs for specific APIs:**
- **Consistent Interface**: Same patterns across all APIs
- **No Vendor Lock-in**: Switch between APIs without learning new patterns
- **Lightweight**: No need for multiple heavy SDKs
- **Customizable**: Full control while maintaining simplicity

**Perfect for:**
- Data engineers working with multiple APIs
- Backend developers building integrations
- Data scientists in notebooks
- DevOps teams automating API interactions

Make Create, Read, Update and Delete operations quickly, easily, and safely. CRUDs
aims to implement URLLib3's best practises while remaining as light as possible.

Features:
 * Authentication: Username & Password, Bearer Token and OAuth2
 * JSON Serialization/Deserialization
 * Request parameters and automatically URL encoded
 * Configurable timeouts (default 5 minutes)
 * Exceptions handling for bad status codes
 * Built-in retry logic with exponential backoff
 * SSL Certificate Verification
 * Logging for monitoring
 * Interfaces (SDK Creation)

### Interfaces

CRUDs provides pre-configured interfaces for popular APIs, making integration even easier:

* **PlanHat** - Complete customer success platform interface with 20+ data models, bulk operations, and advanced analytics. [View Documentation](https://cruds.readthedocs.io/en/latest/interfaces.html#planhat)

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
