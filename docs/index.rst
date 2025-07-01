.. CRUDs documentation master file, created by
   sphinx-quickstart on Thu Aug  8 10:58:11 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

===============================
"Create, Read, Update, Delete"s
===============================

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

**CRUDs** is a high level client library for APIs written in Python, and is ideal for back-end
communication, automated data processing and interactive environments like Notebooks.

--------------------

    >>> import cruds
    >>>
    >>> catfact_ninja = cruds.Client("catfact.ninja")
    >>>
    >>> data = catfact_ninja.read("fact")
    >>> type(data)  # Python built-in data types you can use instantly!
    <class 'dict'>

Make Create, Read, Update and Delete operations quickly, easily, and safely. CRUDs
aims to implement URLLib3's best practices while remaining as light as possible.

Features:
 - Authentication: Username & Password, Bearer Token and OAuth2
 - JSON Serialization/Deserialization
 - Request parameters and automatically URL encoded
 - Configurable timeouts (default 5 minutes)
 - Exceptions handling for bad status codes
 - Built-in retry logic with exponential backoff
 - SSL Certificate Verification
 - Logging for monitoring
 - Interfaces (SDK Creation)

Purpose
-------

The purpose of this package is to simplify the process of interacting with APIs that implement CRUD (Create, Read, Update, Delete) operations.
By using this package, developers can focus more on working with data rather than understanding complex web protocols.

What CRUDs is not:
 - A low-level client library that requires extensive coding for common requirements and production readiness.
 - A high-level client library designed for accessing websites and front-ends, which may contain unnecessary functionality for API usage. (Additional packages may still be required for common functionality)
 - A client library that should be used for APIs that do not follow CRUD operation designs.

What CRUDs is:
 - A high-level client library specifically designed for APIs that implement CRUD operations.
 - A self-contained package that facilitates communication with APIs.
 - Utilizes low-level libraries with minimal overhead.
 - Follows best practices of low-level libraries and protocols to ensure reliability.

By utilizing CRUD operations in API design, this package promotes a more meaningful relationship in the code, rather than relying on web methods such as GET, POST, PUT, PATCH, and DELETE.

Why Choose CRUDs?
-----------------

When working with APIs, you have several HTTP library options. Here's why CRUDs might be the right choice for your project:

**vs. requests/httpx/urllib3:**
 - **Semantic API Design**: Instead of thinking about HTTP methods (GET, POST, PUT, DELETE), think about what you're doing (create, read, update, delete)
 - **Production-Ready Out of the Box**: Built-in retry logic, proper exception handling, and logging without additional configuration
 - **Simplified Authentication**: OAuth2 flows, bearer tokens, and basic auth handled automatically with minimal setup
 - **Data-First Approach**: Returns Python data structures directly instead of response objects requiring manual parsing

**vs. SDKs for specific APIs:**
 - **Consistent Interface**: Same patterns across all APIs you work with
 - **No Vendor Lock-in**: Switch between APIs without learning new SDK patterns
 - **Lightweight**: No need to install multiple heavy SDKs for different services
 - **Customizable**: Full control over requests while maintaining simplicity

**vs. Building your own HTTP wrapper:**
 - **Battle-tested**: Built on urllib3 with proven reliability
 - **Security-focused**: SSL verification, OAuth2 security features, and encryption
 - **Maintained**: Regular updates and security patches
 - **Documented**: Comprehensive documentation and examples

**Perfect for:**
 - Data engineers working with multiple APIs
 - Backend developers building API integrations
 - Data scientists working in notebooks
 - DevOps teams automating API interactions
 - Anyone who wants to focus on data rather than HTTP details

**Example Comparison:**

.. code-block:: python

    # With requests - you need to handle everything manually
    import requests

    response = requests.get("https://api.example.com/users",
                          headers={"Authorization": "Bearer token"},
                          params={"limit": 10})
    response.raise_for_status()
    users = response.json()

    # With CRUDs - focus on the data
    import cruds

    api = cruds.Client("https://api.example.com", auth="token")
    users = api.read("users", params={"limit": 10})

User Guide
----------

General information that will assist in getting the CRUDs package installed,
and examples of way to use it to move data.

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
