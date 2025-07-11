============
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

If you would like to install the latest unreleased source code you can clone it from
`Github CRUDs repository <https://github.com/johnbrandborg/cruds>`_.

Using a git client you can clone the repository and install it with pip like so::

    $ git clone https://github.com/johnbrandborg/cruds.git
    $ python -m pip install ./cruds

For developers wanting to contribute, please visit the :ref:`development` section.

=============
General Usage
=============

Unlike other HTTP packages that require the full URL and methods as arguments with
every request, with CRUDs the object you create is a representation of a platform
interface.  In it's most basic from only the host name is required when creating
your client instance.

.. code-block:: python

    from cruds import Client

    api = Client("https://host/")

When creating the client all features can be adjusted to suit most needs. Refer
to the module contents of :py:class:`cruds.Client` for more information.

.. code-block:: python

    # Disable retries and set the required timeout to 20 seconds
    api = Client("https://host/", retries=0, timeout=20)

    # Send & receive raw data and never raise an exception on bad status codes
    api = Client("https://host/", serialize=False, raise_status=False)

    # Disable SSL Verification
    api = Client("https://host/", verify_ssl=False)

By default CRUDs will raise an exception if it is not able to give you your
data.  While uncommon if required to ignore a status code raising an exception
you can do this by adding and removing that status code into the ignore set:

.. code-block:: python

    api.status_ignore.add(409)
    api.status_ignore.remove(409)

Once the client has been created, CRUD requests can be made by supplying URI's,
data & params with Dictionaries.

**Example**

.. code-block:: python

    user = "/api/v1/user"

    # Create a User
    api.create(user, data={"name": "fred"}, params={"company_id": "1003"})

    # Read User details
    fred = api.read(user, params={"name": "fred", "select": "id"})

    # Update the User details
    api.update(f"{user}/{fred}", data={"name": "Fred"})

    # Delete the User
    api.delete(f"{user}/{fred}")

While most HTTP clients require you to handle web response objects and deal with
issues, retries, and data extraction, our CRUD Client methods simplify the process
by only returning the necessary data. In the event of a request issue, an error
will be raised, ensuring a more efficient and streamlined experience.

Comparison with Other Libraries
------------------------------

Here are detailed comparisons showing how CRUDs simplifies common API tasks compared to other popular HTTP libraries.

**Basic API Call**

.. code-block:: python

    # With requests
    import requests

    response = requests.get("https://api.example.com/users/123")
    response.raise_for_status()
    user = response.json()

    # With httpx
    import httpx

    with httpx.Client() as client:
        response = client.get("https://api.example.com/users/123")
        response.raise_for_status()
        user = response.json()

    # With CRUDs
    import cruds

    api = cruds.Client("https://api.example.com")
    user = api.read("users/123")

**Authentication**

.. code-block:: python

    # With requests - manual header management
    import requests

    headers = {"Authorization": "Bearer your-token"}
    response = requests.get("https://api.example.com/users", headers=headers)

    # With CRUDs - automatic token handling
    import cruds

    api = cruds.Client("https://api.example.com", auth="your-token")
    users = api.read("users")

**OAuth2 Authentication**

.. code-block:: python

    # With requests - you need to implement OAuth2 flow yourself
    import requests
    from requests_oauthlib import OAuth2Session

    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)
    authorization_url, state = oauth.authorization_url(auth_url)
    # ... handle redirect, get code, exchange for token
    token = oauth.fetch_token(token_url, client_secret=client_secret)

    response = requests.get("https://api.example.com/users",
                          headers={"Authorization": f"Bearer {token['access_token']}"})

    # With CRUDs - OAuth2 handled automatically
    import cruds
    from cruds.auth import OAuth2

    api = cruds.Client(
        "https://api.example.com",
        auth=OAuth2(
            url="https://api.example.com/oauth/token",
            client_id="your-client-id",
            client_secret="your-client-secret",
            scope="read write"
        )
    )
    users = api.read("users")

**Error Handling and Retries**

.. code-block:: python

    # With requests - manual retry logic
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.get("https://api.example.com/users")
        response.raise_for_status()
        users = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

    # With CRUDs - built-in retry logic and error handling
    import cruds

    api = cruds.Client("https://api.example.com", retries=3)
    users = api.read("users")  # Automatic retries and error handling

**Complex API Operations**

.. code-block:: python

    # With requests - verbose and error-prone
    import requests

    # Create user
    user_data = {"name": "John", "email": "john@example.com"}
    response = requests.post("https://api.example.com/users", json=user_data)
    response.raise_for_status()
    user = response.json()

    # Update user
    update_data = {"name": "John Doe"}
    response = requests.patch(f"https://api.example.com/users/{user['id']}", json=update_data)
    response.raise_for_status()

    # Delete user
    response = requests.delete(f"https://api.example.com/users/{user['id']}")
    response.raise_for_status()

    # With CRUDs - clean and semantic
    import cruds

    api = cruds.Client("https://api.example.com")

    # Create user
    user = api.create("users", data={"name": "John", "email": "john@example.com"})

    # Update user
    api.update(f"users/{user['id']}", data={"name": "John Doe"})

    # Delete user
    api.delete(f"users/{user['id']}")

**Working with Query Parameters**

.. code-block:: python

    # With requests - manual parameter encoding
    import requests
    from urllib.parse import urlencode

    params = {
        "page": 1,
        "limit": 10,
        "filter": "active",
        "sort": "name"
    }
    response = requests.get(f"https://api.example.com/users?{urlencode(params)}")

    # With CRUDs - automatic parameter handling
    import cruds

    api = cruds.Client("https://api.example.com")
    users = api.read("users", params={
        "page": 1,
        "limit": 10,
        "filter": "active",
        "sort": "name"
    })

Method Relationship
-------------------

To make it easier to understand how to use CRUD operations, here is a breakdown
of the relevant web method requests using the Client Class methods. While they
are closely related, there is a minor difference to be aware of.  Generally the
relation is one to one with the exception being ``update``.

By default ``update`` will use a PATCH method which generally indicates only updating
the set of specific values.  An ``update`` may also use the PUT method to perform a
replacement, which can be used by setting ``replace`` to ``True``.

==================== ===========
Client Method        HTTP Method
==================== ===========
create()             POST
read()               GET
update()             PATCH
update(replace=True) PUT
delete()             DELETE
==================== ===========

Authentication
--------------

When authenticating with the Client, the Auth argument will detect how you want
to authenticate.  If you don't use the Auth argument no authentication is used.

If you supply only a string it will be used as a bearer token.  A list or tuple
will be used for Username and Password, and lastly an Auth Class is a complex
Workflow. (eg, See OAuth2 below)

.. code-block:: python

    from cruds import Client

    # Authentication with Token
    api = Client("https://host/", auth="bearer-token")

    # Authentication with Username and Password
    api = Client("https://host/", auth=("username", "password"))

OAuth2 Workflows
^^^^^^^^^^^^^^^^

OAuth 2 is the industry-standard protocol for authorization.  CRUDs supports the
Authorization Flows:

 1. Client Credentials
 2. Resource Owner Password (if username and password arguments are supplied)
 3. Authorization Code (with state parameter for CSRF protection)

When an expiry time is returned by the server with the access token refreshing
is taken care of automatically, along with using refresh tokens.

**Security Features:**

- **Token Encryption**: All token state is encrypted in memory using Fernet encryption
- **Custom Encryption Keys**: You can provide your own encryption key for enhanced security
- **Automatic Key Derivation**: If no custom key is provided, a key is derived from the client_secret
- **State Parameter**: CSRF protection for Authorization Code flow using cryptographically secure state parameters

.. code-block:: python

    from cruds import Client
    from cruds.auth import OAuth2

    # Basic OAuth2 with automatic key derivation
    api = Client(
        host="https://host/",
        auth=OAuth2(
            url="https://host/token",
            client_id="id",
            client_secret="secret",
            scope="all-apis",
            # Rich Authorization Requests (RAR)
            authorization_details=[
                {
                    "type":  "permissions",
                    "operation": "read",
                }
            ]
        )
    )

    # OAuth2 with custom encryption key (recommended for production)
    api = Client(
        host="https://host/",
        auth=OAuth2(
            url="https://host/token",
            client_id="id",
            client_secret="secret",
            scope="all-apis",
            encryption_key="your-32-character-encryption-key-here"
        )
    )

    # Authorization Code flow with state parameter (most secure for user-facing apps)
    oauth = OAuth2(
        url="https://host/token",
        client_id="id",
        client_secret="secret",
        scope="all-apis",
        authorization_url="https://host/authorize",
        redirect_uri="https://your-app.com/callback",
        encryption_key="your-32-character-encryption-key-here"
    )

    # Step 1: Generate authorization URL with state parameter
    auth_url = oauth.get_authorization_url()
    # Redirect user to auth_url

    # Step 2: After user authorization, parse the redirect response
    redirect_url = "https://your-app.com/callback?code=abc123&state=xyz789"
    code, state = oauth.parse_authorization_response(redirect_url)

    # Step 3: Exchange authorization code for access token
    access_token = oauth.exchange_code_for_token(code, state)

    # Use the OAuth2 instance with the Client
    api = Client(host="https://host/", auth=oauth)

.. note::

  The OAuth 2.0 framework will take time to implement and implemented properly.
  Support in improving this coverage is very welcome. Let the project know of
  any Issues.

.. note::

  For production environments, it's recommended to provide a custom encryption_key
  rather than relying on automatic key derivation from client_secret.

.. note::

  The Authorization Code flow with state parameter is the most secure OAuth flow
  for user-facing applications, providing CSRF protection and following OAuth 2.0
  security best practices.

Serialize
---------

By default the Client of the API will attempt to Serialize and Deserialize JSON
into and from Python built-in data types.  Lists and Dictionaries with basic data
types like boolean, floats, integers, and strings can be on the data argument,
and the returned data is the same.

The API however needs to indicate the content type is JSON! If not the Client will
attempt to return JSON, and will fall-back to returning the bytes type data if
deserialization fails, pressuming that ``serialize`` is enabled by mistake.

If the Client has serialization disabled only the string or byte types are taken
as data, and the return is bytes type data.

.. note::

    If there is a need to expand on the SerDes content types, please raise a
    issue in the Github repository so the project is aware of it.

Retries
-------

Connections, reads, redirects, and bad status codes are implemented in the CRUDs
Client to perform retries.  If any of these are encounted a retry will take place
a total of 4 times across the different types.
Each retry will also backoff by a factor of 0.9 after the second attempt.  This
can give the communication between the client and server time to get established
or recover from being rate limited.

Status Codes:

 - 408 Request Timeout
 - 425 Too Early
 - 429 Too Many Requests  (Rate Limited)
 - 500 Internal Server Error
 - 502 Bad Gateway
 - 503 Service Unavailable
 - 504 Gateway Timeout

You can adjust the retries, backoff_factor and retry_status_codes on the Client
with arguments.  If you increase the retries, consider reducing the backoff amount
to avoid large delays, however no backoff will ever be longer the maximum of 120
seconds.

Logging
-------

Because CRUDs is high level it has verbose logging to assist with capturing
information around general operations.

If you want to see logging set the level to INFO using the logging module as shown,
below before you create the Client instance.

**Recommended**

.. code-block:: python

    import logging

    logging.basicConfig(level=logging.INFO)

Setting the level to ``logging.DEBUG`` will show you URLLib3 messages which is
a useful way to see what calls CRUDs makes to URLLib3.

Extensibility
-------------

The library has been created with extensibility in mind, so that Software Development
Kits can be created.  There are two ways that this can be done, one as described below
or by creating an 'Interface As Code'.

The basic approach is to create a new subclass and add the logic requirements needed to
make the requests.  You are effectively just adding the host name into the
initialization and the URI into the methods:

.. code-block:: python

    from cruds import Client

    class CatFactNinja(Client):
        """Cat Fact Ninja Interface"""

        # Use private attributes for storing common URI's.
        _fact_uri = "fact"

        def __init__(self, **kwargs):
            # Init Super with host name with kwargs
            super().__init__("http://catfact.ninja/", **kwargs)

        @property
        def fact(self):
            """ Get a Fact about Cats"""
            return self.read(self._fact_uri).get("fact")

    cat = CatFactNinja()
    print(cat.fact)

**Interfaces**

CRUDs also supports creating interfaces (basically SDKs) with large amounts of
models as a mixture of YAML configuration and functions for the common logic.
This significantly reduces the amount of python coding needed, and the common
methods can be reused.

For more information on Interfaces that come with CRUDs and how to create them
visit the :ref:`interfaces` page.
