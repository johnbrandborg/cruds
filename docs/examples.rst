Examples
========

Here you can find code snippets that show how easy it is to work with some platforms.

Databricks
----------

Serverless OLTP Database - PostgREST
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
