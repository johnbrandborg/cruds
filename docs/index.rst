.. CRUDs documentation master file, created by
   sphinx-quickstart on Thu Aug  8 10:58:11 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

"Create, Read, Update, Delete"s
===============================

Release v\ |version|.

.. image:: https://img.shields.io/pypi/pyversions/cruds?logo=python&logoColor=FFE873
    :target: https://pypi.org/project/cruds/
    :alt: Supported Python Version

.. image:: https://img.shields.io/pypi/dm/cruds
    :target: https://pypistats.org/packages/cruds
    :alt: PyPI downloads

.. image:: https://img.shields.io/pypi/l/cruds.svg
    :target: https://github.com/johnbrandborg/cruds/blob/main/LICENSE
    :alt: License Badge

**CRUDs** is a high level library for API's, and is ideal for automated data processing
and interactive environments like Notebooks.

--------------------

    >>> import cruds
    >>>
    >>> catfact_ninja = cruds.Client(host="https://catfact.ninja/")
    >>>
    >>> data = catfact_ninja.read("fact")
    >>> type(data)  # Python built-in data types you can use straight away!
    <class 'dict'>

Make Create, Read, Update and Delete operations quickly, easily, and safely. CRUDs
aims to handle the majority of the setup needed for production so you can focus
on moving data.

Features:
 - Authentication with a bearer token, username & password, or OAuth2
 - Data serialization/de-serialization (Currently only JSON format)
 - Request parameters as Dictionaries and automatically URL encoded
 - Default connection timeout (5 minutes)
 - Raises exceptions on bad status codes (Can be whitelisted)
 - Retries with back-off
 - SSL Verification
 - Logging for monitoring
 - Interfaces (SDK Creation)

User Guide
----------

General information that will assist in getting the CRUDs package installed,
and examples of way to use it to move data.

.. toctree::
   :maxdepth: 2

   user_guide
   authentication
   interfaces
   changelog
   development
   license

API Documentation
-----------------

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
