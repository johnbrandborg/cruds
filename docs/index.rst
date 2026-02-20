.. CRUDs documentation master file, created by
   sphinx-quickstart on Thu Aug  8 10:58:11 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

====
CRUDs
====

Release v\ |version|

.. image:: https://img.shields.io/pypi/pyversions/cruds?logo=python&logoColor=FFE873
    :target: https://pypi.org/project/cruds/
    :alt: Supported Python Version

.. image:: https://img.shields.io/pypi/dm/cruds
    :target: https://pypistats.org/packages/cruds
    :alt: PyPI downloads

.. image:: https://img.shields.io/pypi/l/cruds.svg
    :target: https://github.com/johnbrandborg/cruds/blob/main/LICENSE
    :alt: License Badge

**CRUDs** is a lightweight Python client for REST APIs — create, read, update,
and delete with zero boilerplate.

--------------------

Quickstart
----------

Install from PyPI::

    $ pip install cruds

Then start talking to any API:

.. code-block:: python

    import cruds

    api = cruds.Client("https://api.example.com", auth="your-token")

    # Create
    user = api.create("users", data={"name": "Ada", "role": "engineer"})

    # Read
    user = api.read(f"users/{user['id']}")

    # Update
    api.update(f"users/{user['id']}", data={"role": "lead"})

    # Delete
    api.delete(f"users/{user['id']}")

No response objects to unpack. No manual JSON parsing. No boilerplate retry
logic. Just your data.

Why CRUDs?
----------

**Batteries included, boilerplate removed.**

Most HTTP libraries make you handle serialization, error checking, retries,
and auth yourself. CRUDs handles all of that out of the box so you can focus
on the data:

.. code-block:: python

    # With requests — ceremony
    import requests
    response = requests.get("https://api.example.com/users",
                            headers={"Authorization": "Bearer token"})
    response.raise_for_status()
    users = response.json()

    # With CRUDs — intent
    import cruds
    users = cruds.Client("api.example.com", auth="token").read("users")

Features:
 - **Authentication** — Bearer tokens, username/password, and OAuth2 (Client
   Credentials, Resource Owner Password, Authorization Code with CSRF)
 - **JSON Serialization** — Send and receive Python dicts and lists directly
 - **Retries with backoff** — Configurable count, backoff factor, and status
   codes (429, 500–504, etc.)
 - **Error handling** — Automatic exceptions for 4xx/5xx responses
 - **SSL verification** — Enabled by default via certifi
 - **Logging** — Built-in INFO/DEBUG logging for monitoring
 - **Interfaces** — Build SDKs with YAML configuration (ships with a full
   Planhat interface)

For detailed comparisons with requests, httpx, and other libraries, see the
:ref:`user_guide` section on
:ref:`comparisons <comparison-with-other-libraries>`.

User Guide
----------

.. toctree::
   :maxdepth: 2

   user_guide
   interfaces
   examples
   changelog
   development
   license

API Reference
-------------

For developers searching for information relating more closely to code

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
