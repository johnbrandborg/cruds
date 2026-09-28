Planhat
=======

Planhat is a customer success platform. CRUDs provides a Planhat Interface for
the models and operations listed below.

See Planhat's `official developer documentation
<https://www.planhat.com/developers>`_ for API details.

API endpoints
-------------

* Main API: https://api.planhat.com/
* Analytics API: https://analytics.planhat.com/

Authentication
--------------

* API token authentication for the main API
* Tenant token authentication for analytics endpoints
* Analytics-only clients may omit the API token
* Configurable rate limiting (default: 200 calls per minute)

Getting started
---------------

Create a client with your API token, then access each model as an attribute:

.. code-block:: python

    from cruds.interfaces.planhat import Planhat

    planhat = Planhat(api_token="your-api-token")

    company = planhat.company.get_by_id("extid-your-company-id")

    for page in planhat.company.get_list(limit=100, select=None):
        for company in page:
            print(company["_id"], company["name"])

``get_list()`` yields one page at a time and continues until Planhat returns an
empty page. Use ``max_requests`` to limit the number of API requests:

.. code-block:: python

    first_page = next(planhat.company.get_list(max_requests=1))

Supply a tenant token when using analytics models:

.. code-block:: python

    planhat = Planhat(
        api_token="your-api-token",
        tenant_token="your-tenant-token",
    )

**Core Features Supported:**

**Data Models (20+ entities):**

* **Asset** - Track nested objects like product instances, devices, or custom entities
* **Campaign** - Manage customer campaigns and adoption initiatives
* **Churn** - Log customer churn events and reasons
* **Company** - Core customer accounts with hierarchical structure support
* **Conversation** - Email, chat, support tickets, and custom communication types
* **Custom_Field** - Extend any object with custom properties
* **Enduser** - Individual contacts at customer companies with domain auto-assignment
* **Invoice** - Track billing and invoicing history
* **Issue** - Bug reports and feature requests (Jira integration support)
* **License** - Subscription management with MRR/ARR calculations
* **Deal** - Sales opportunities and contracts
* **Line_Item** - Subscription and fee line items attached to deals
* **Product** - Reusable subscription and fee templates
* **Metrics** - Dimension data for customer success metrics
* **NPS** - Net Promoter Score survey responses and scoring
* **Note** - Manual notes and conversation logging
* **Objective** - Customer success goals and health tracking
* **Opportunity** - Sales opportunities and expansion tracking
* **Project** - Time-bound initiatives with custom fields
* **Sale** - Non-recurring revenue tracking
* **Task** - Task management with calendar integration
* **Ticket** - Support ticket management with external system sync
* **Time_Entry** - Time logs; includes ``duplicate()`` for bulk duplicate by id
* **Timesheet** - Collections of time entries per user
* **User** - Team member management and access control
* **Workspace** - Sub-instance tracking for multi-department engagement

**Standard CRUD Operations:**

Most main-API models support the following operations:

* ``create()`` - Create new records
* ``update()`` - Update existing records by ID, External ID, or Source ID
* ``get_by_id()`` - Retrieve records by ID, External ID, or Source ID
* ``get_list()`` - Retrieve paginated lists with filtering and sorting
* ``delete()`` - Remove records
* ``bulk_upsert()`` - Batch create/update operations (up to 5,000 items per request)

``get_list()`` preserves the historical ``"name, companyId"`` field selection by default.
Pass ``select=None`` to retrieve all fields, including for models with different schemas such
as ``Line_Item`` and ``Product``.

There are model-specific exceptions:

* ``Custom_Field`` does not expose ``bulk_upsert()``
* ``Ticket`` exposes ``bulk_upsert()``, ``get_list()``, and ``delete()``
* ``Metrics`` and ``user_activity`` use the analytics operations documented below

**Specialized Methods:**

**Company Model:**

* ``get_lean_list()`` - Lightweight company list for ID matching

**Metrics Model:**

* ``epoch_days_format()`` - Convert dates to epoch days format
* ``get_dimension_data()`` - Retrieve time-series metrics data
* ``bulk_insert_metrics()`` - Batch insert metrics with auto-chunking

**User Activity Model:**

* ``create_activity()`` - Track user engagement events
* ``segment()`` - User segmentation and analytics

**Advanced Features:**

**Bulk Operations:**

* Auto-chunking for large datasets
* Main-API bulk chunk sizes validated against Planhat's 5,000-item limit
* Aggregated responses are retained on the owning ``Planhat`` client
* Optional ``raise_on_error=True`` for bulk response validation
* Main-API rate limiting with delays between requests
* Analytics payload sizing below Planhat's 32 MB body limit

**Data Formatting:**

* Epoch days date format support
* External ID and Source ID reference support
* Custom field extensibility

**Integration Capabilities:**

* CRM system synchronization (Salesforce, etc.)
* Ticketing system integration (Zendesk, etc.)
* Product management tool integration (Jira, Product Board, Aha!)
* NPS tool imports
* Calendar system integration (Google Calendar)
* Webhook support for real-time data sync

**Error Handling:**

* Custom exception classes for bulk operations
* Aggregated bulk error reporting through ``PlanhatUpsertError``
* Automatic retry mechanisms

Specialized examples
--------------------

.. code-block:: python

    licenses = [
        {"name": "Premium Plan", "companyId": "extid-123", "value": 1000},
        {"name": "Basic Plan", "companyId": "extid-456", "value": 500},
    ]
    result = planhat.license.bulk_upsert(licenses, raise_on_error=True)

    activity = {
        "event": "login",
        "userId": "user123",
        "companyId": "extid-123",
        "timestamp": "2024-01-15T10:30:00Z",
    }
    planhat.user_activity.create_activity(activity)

    metrics = {
        "dimensionId": "daily_logins",
        "companyId": "extid-123",
        "value": 150,
        "time": "2024-01-15T00:00:00Z",
    }
    planhat.metrics.bulk_insert_metrics([metrics])

The configuration file for this Interface can be found on
`Github <https://github.com/johnbrandborg/cruds/blob/main/src/cruds/interfaces/planhat/configuration.yaml>`_.
