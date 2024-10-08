Installation
============

This part of the documentation covers the installation of CRUDs.
The first step to using any software package is getting it properly installed.

$ pip install cruds
-------------------

To install a stable version of CRUDs, use pip by running the following command::

    $ python -m pip install cruds

If you have installed Python, then pip should be available.  If not visit
`getting-started <https://pip.pypa.io/en/stable/getting-started/>`_ with pip.

Source Code
-----------

If you would like to install an latest unreleased source code you can clone it from
`Github <https://github.com/johnbrandborg/cruds>`_.

Using a git client you can clone the repository and install it with pip::

    $ git clone https://github.com/johnbrandborg/cruds.git
    $ python -m pip install ./cruds

For developers wanting to contribute, please visit the :ref:`development` section.

General Usage
=============

Unlike other HTTP packages that you have handle the full URL and methods, with
CRUDs the object you create is a representation of an API.  You can then interact
with the API using CRUD operations.

All features can be adjusted on the Client to suit most needs.

    >>> from cruds import Client
    >>>
    >>> # Authentication with Username and Password
    >>> api = Client(host="https://localhost/api/v1/",
    ...          auth=("username", "password"))
    >>>
    >>> # Authentication with Token
    >>> api = Client(host="https://localhost/api/v1/",
    ...          auth="bearer-token")
    >>>
    >>> # Send and receive raw data and ignore bad status codes
    >>> api = Client(host="https://localhost/api/v1/",
    ...          serialize=False,
    ...          raise_status=False)
    >>>
    >>> # Disable SSL Verification
    >>> api = Client(host="https://localhost/api/v1/",
    ...          verify_ssl=False)

Once the client has been created, CRUD requests can be made by supplying URI's,
data & params with Dictionaries.

**Example**

    >>> # Create a User
    >>> api.create(uri="user", data={"name": "fred"}, params={"company_id": "1003"})
    >>>
    >>> # Update the User details
    >>> id = api.read(uri="user", params={"name": "fred", "select": "id"})
    >>> api.update(uri=f"user/{id}", data={"name": "Fred"})
    >>>
    >>> # Delete the User
    >>> api.delete(uri=f"user/{id}")

By default `update` will use a PATCH method which generally indicates only updating
the set of specific values.  An `update` may also use the PUT method to perform a
replacement, which can be used by setting `replace` to True.

Logging
-------

Because CRUDs is high level it has verbose logging to assist with capturing
information around general operations.

If you want to see logging set the level using the standard logging interface.
DEBUG will show you URLLib3, but INFO will give you general information from
the CRUDs Client.

    >>> import logging
    >>> import cruds
    >>>
    >>> logging.basicConfig(level=logging.INFO)

Extensibility
-------------

The library has been created with extensibility in mind, so that Software Development
Kits can be created.  There is two ways that this can be done, one as described below
or by creating an Interface.

The basic approach is to create a new class and add the logic requirements needed to
make the requests.

    >>> from cruds import Client
    >>>
    >>> class CatFactNinja(Client):
    ...     """Cat Fact Ninja Interface"""
    ...
    ...     _fact_uri = "fact"
    ...
    ...     def __init__(self, **kwargs):
    ...         host = "http://catfact.ninja/"
    ...         super().__init__(host=host, **kwargs)
    ...
    ...     @property
    ...     def fact(self):
    ...         """ Get a Fact about Cats"""
    ...         return self.read(self._fact_uri)
    >>>
    >>> cat = CatFactNinja()
    >>> print(cat.fact)

CRUDs supports creating interfaces with large amounts of models as a mixture of
YAML configuration and functions for the common logic.  This significantly
reduces the amount of python coding needed, and the common methods can be reused.
