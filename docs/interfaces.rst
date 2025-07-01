.. _interfaces:

Interfaces
==========

Within CRUDs pre-configured Interfaces have been created. To use an Interface
import them from interface packages under ``cruds.interfaces.<name>``.

Currently available:

* Planhat

Planhat
-------

Planhat is a comprehensive customer success platform with immense capabilities. CRUDs offers a
full implementation of the Planhat platform as an Interface, providing complete API coverage
for all major Planhat features and data models.

**Official Documentation URL:** https://docs.planhat.com/

**API Endpoints:**

* Main API: https://api.planhat.com/
* Analytics API: https://analytics.planhat.com/

**Authentication:**

* Primary authentication via API token
* Secondary authentication via tenant token for analytics endpoints
* Configurable rate limiting (default: 200 calls per minute)

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
* **Metrics** - Dimension data for customer success metrics
* **NPS** - Net Promoter Score survey responses and scoring
* **Note** - Manual notes and conversation logging
* **Objective** - Customer success goals and health tracking
* **Opportunity** - Sales opportunities and expansion tracking
* **Project** - Time-bound initiatives with custom fields
* **Sale** - Non-recurring revenue tracking
* **Task** - Task management with calendar integration
* **Ticket** - Support ticket management with external system sync
* **User** - Team member management and access control
* **Workspace** - Sub-instance tracking for multi-department engagement

**Standard CRUD Operations:**

All models support the following operations:

* ``create()`` - Create new records
* ``update()`` - Update existing records by ID, External ID, or Source ID
* ``get_by_id()`` - Retrieve records by ID, External ID, or Source ID
* ``get_list()`` - Retrieve paginated lists with filtering and sorting
* ``delete()`` - Remove records
* ``bulk_upsert()`` - Batch create/update operations (up to 5,000 items per request)

**Specialized Methods:**

**Company Model:**

* ``get_lean_list()`` - Lightweight company list for ID matching

**Metrics Model:**

* ``epoc_days_format()`` - Convert dates to epoch days format
* ``get_dimension_data()`` - Retrieve time-series metrics data
* ``bulk_insert_metrics()`` - Batch insert metrics with auto-chunking

**User Activity Model:**

* ``create_activity()`` - Track user engagement events
* ``segment()`` - User segmentation and analytics

**Advanced Features:**

**Bulk Operations:**

* Auto-chunking for large datasets
* Configurable chunk sizes
* Response aggregation and error handling
* Rate limiting with automatic delays

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
* Comprehensive error reporting
* Automatic retry mechanisms

Example Usage:

.. code-block:: python

    >>> from cruds.interfaces.planhat import Planhat
    >>>
    >>> # Initialize with API token and optional tenant token
    >>> planhat = Planhat(
    ...     api_token="hJA4eO3tJPhDck1aKLvQ5osvNUfKYdJ7H",
    ...     tenant_token="1d5df0f5-f217-49da-8997-2878f5986a9f"
    ... )
    >>>
    >>> # Get comprehensive help
    >>> help(planhat)
    >>>
    >>> # Retrieve a company by external ID
    >>> company = planhat.company.get_by_id("extid-21432948")
    >>>
    >>> # Bulk upsert licenses
    >>> licenses_data = [
    ...     {"name": "Premium Plan", "companyId": "extid-123", "value": 1000},
    ...     {"name": "Basic Plan", "companyId": "extid-456", "value": 500}
    ... ]
    >>> result = planhat.license.bulk_upsert(licenses_data)
    >>>
    >>> # Track user activity
    >>> activity_data = {
    ...     "event": "login",
    ...     "userId": "user123",
    ...     "companyId": "extid-123",
    ...     "timestamp": "2024-01-15T10:30:00Z"
    ... }
    >>> planhat.user_activity.create_activity(activity_data)
    >>>
    >>> # Insert metrics data
    >>> metrics_data = {
    ...     "dimensionId": "daily_logins",
    ...     "companyId": "extid-123",
    ...     "value": 150,
    ...     "time": "2024-01-15T00:00:00Z"
    ... }
    >>> planhat.metrics.bulk_insert_metrics([metrics_data])

The configuration file for this Interface can be found on
`Github <https://github.com/johnbrandborg/cruds/blob/main/src/cruds/interfaces/planhat/configuration.yaml>`_.
