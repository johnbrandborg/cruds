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
    >>> catfact_ninja = cruds.Client("https://catfact.ninja/")
    >>>
    >>> data = catfact_ninja.read("fact")
    >>> type(data)  # Python built-in data types you can use instantly!
    <class 'dict'>

Make Create, Read, Update and Delete operations quickly, easily, and safely. CRUDs
aims to handle the majority of the setup needed for production so you can focus
on moving data.

Features:
 - Authentication: Username & Password, Bearer Token or OAuth2
 - JSON Serialization/Deserialization
 - Request parameters and automatically URL encoded
 - Default connection timeout (5 minutes)
 - Raises exceptions on bad status codes
 - Retries with back-off
 - SSL Verification
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
