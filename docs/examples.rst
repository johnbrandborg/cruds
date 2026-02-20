Examples
========

Here you can find code snippets that show how easy it is to work with various
platforms and public APIs.

JSONPlaceholder (Try It Now)
----------------------------

`JSONPlaceholder <https://jsonplaceholder.typicode.com/>`_ is a free fake REST
API — perfect for testing CRUDs without any API keys.

.. code-block:: python

    import cruds

    api = cruds.Client("jsonplaceholder.typicode.com")

    # Read all posts
    posts = api.read("posts", params={"_limit": 5})
    print(f"Got {len(posts)} posts")

    # Create a new post
    new_post = api.create("posts", data={
        "title": "Hello from CRUDs",
        "body": "This was easy.",
        "userId": 1,
    })
    print(f"Created post #{new_post['id']}")

    # Update the post
    api.update(f"posts/{new_post['id']}", data={"title": "Updated title"})

    # Delete the post
    api.delete(f"posts/{new_post['id']}")

GitHub API
----------

Read public repository data from the GitHub REST API.

.. code-block:: python

    import cruds

    github = cruds.Client("api.github.com")

    # Get repository info (no auth needed for public repos)
    repo = github.read("repos/johnbrandborg/cruds")
    print(f"{repo['full_name']} — {repo['stargazers_count']} stars")

    # List recent commits
    commits = github.read("repos/johnbrandborg/cruds/commits", params={"per_page": 5})
    for commit in commits:
        print(f"  {commit['sha'][:7]} {commit['commit']['message'].splitlines()[0]}")

With a personal access token you can access private resources:

.. code-block:: python

    github = cruds.Client("api.github.com", auth="ghp_your_token_here")
    user = github.read("user")
    print(f"Authenticated as {user['login']}")

Weather API
-----------

Fetch weather data from the free `Open-Meteo <https://open-meteo.com/>`_ API
(no API key required).

.. code-block:: python

    import cruds

    weather = cruds.Client("api.open-meteo.com")

    forecast = weather.read("v1/forecast", params={
        "latitude": -33.87,
        "longitude": 151.21,
        "current_weather": True,
    })

    current = forecast["current_weather"]
    print(f"Sydney: {current['temperature']}°C, wind {current['windspeed']} km/h")

Authenticated API with OAuth2
-----------------------------

For APIs that require OAuth2 Client Credentials (common in B2B integrations):

.. code-block:: python

    from cruds import Client
    from cruds.auth import OAuth2

    api = Client(
        host="https://api.example.com",
        auth=OAuth2(
            url="https://api.example.com/oauth/token",
            client_id="your-client-id",
            client_secret="your-client-secret",
            scope="read write",
        ),
    )

    data = api.read("protected/resource")

CRUDs handles token acquisition, caching, and refresh automatically.

Databricks
----------

Serverless OLTP Database - PostgREST
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Currently in Private Preview from Databricks, however it offers a Service URL which
is an API that with Service Principal OAuth2 credentials can read data from the database.

**Online Table Example**

.. code-block:: python

    from os import getenv

    from cruds import Client
    from cruds.auth import OAuth2


    WORKSPACE: str = "dbc-39f83jfs-12f0"
    CATALOG: str = "main"
    SCHEMA: str = "default"
    TABLE: str = "ot_model"
    ONLINE_TABLE: str = f"/api/2.0/workspace/8329472938749342/online/pgrest/{CATALOG}/{TABLE}"


    online_table =  Client(
        host="https://1239ds8f-asda-asd2-192d-04jf821923ab.online-tables.cloud.databricks.com/",
        auth=OAuth2(
            url=f"https://{WORKSPACE}.cloud.databricks.com/oidc/v1/token",
            client_id=getenv("DB_CLIENT_ID"),
            client_secret=getenv("DB_CLIENT_SECRET"),
            scope='all-apis',
            authorization_details=[
                {
                    "type": "unity_catalog_permission",
                    "securable_type": "table",
                    "securable_object_name": f"{CATALOG}.{SCHEMA}.{TABLE}",
                    "operation":"ReadOnlineView"
                }
            ]
        )
    )
    online_table.request_headers.add("Accept-Profile", SCHEMA)

    data = online_table.read(ONLINE_TABLE, {"limit": 3})
