Kolleno
=======

CRUDs provides a Kolleno Open API v1 Interface covering the resources published
in Kolleno's `Postman documentation
<https://documenter.getpostman.com/view/43609274/2sBYAvvVnT>`_.

Authentication
--------------

Kolleno API keys contain a client ID and client secret. The Interface sends
them using Kolleno's ``Authorization: API client_id:client_secret`` header.
By default, requests are sent to ``https://api.kolleno.com/v1``. You can
override ``domain_name`` if your account uses a different API base URL.

.. code-block:: python

    from cruds.interfaces.kolleno import Kolleno

    kolleno = Kolleno(
        client_id="your-client-id",
        client_secret="your-client-secret",
    )

Resource paths
--------------

Kolleno resources are hierarchical. Pass identifiers in the same order they
appear in the documented URL:

.. code-block:: python

    # GET /company/
    companies = kolleno.company.get_list(limit=100, offset=0)

    # GET /customer/{company}/{customer}/
    customer = kolleno.customer.get_by_id("company-id", "customer-id")

    # POST /invoice/{company}/
    invoice = kolleno.invoice.create(
        "company-id",
        data={
            "customer": "customer-id",
            "amount": "100.00",
            "currency": "GBP",
        },
    )

    # PATCH /person/company/{company}/{person}/
    person = kolleno.person.update(
        "company-id",
        "person-id",
        data={"primary": True},
    )

    # DELETE /transaction/{customer}/{transaction}/
    kolleno.transaction.delete("customer-id", "transaction-id")

Dynamic path values are URL-escaped by the Interface. Query parameters are
passed as keyword arguments to ``get_list()``:

.. code-block:: python

    customers = kolleno.customer.get_list(
        "company-id",
        fields="source_id,balance",
        limit=50,
        offset=0,
    )

Pagination
----------

Kolleno list responses use ``count``, ``next``, ``previous``, and ``results``.
Use ``get_all()`` to iterate through every result using offset pagination:

.. code-block:: python

    for invoice in kolleno.invoice.get_all("company-id", limit=100):
        print(invoice["id"])

Files and specialized resources
-------------------------------

Invoice PDFs support multipart upload. Download resources return bytes when
Kolleno responds with a file:

.. code-block:: python

    uploaded = kolleno.invoice_pdf.create(
        "invoice-id",
        data={},
        files={
            "file": (
                "invoice.pdf",
                invoice_bytes,
                "application/pdf",
            )
        },
    )

    invoice_pdf = kolleno.invoice_pdf_download.download(
        "company-id",
        "invoice-id",
    )
    credit_note_pdf = kolleno.credit_note_pdf.download(
        "company-id",
        "credit-note-id",
    )
    report = kolleno.report_file.download("company-id", "report-file-id")

Models
------

The Interface includes:

* ``company``
* ``card_detail`` and ``direct_debit_detail``
* ``customer``, ``customer_portal``, and ``customer_custom_fields``
* ``credit_note`` and ``credit_note_pdf``
* ``invoice``, ``invoice_custom_fields``, ``invoice_pdf``, and
  ``invoice_pdf_download``
* ``match``
* ``person`` and ``person_invoice``
* ``position_external``
* ``report_file``
* ``tag`` and ``tag_category``
* ``transaction``
* ``timeline``

Most writable models expose ``get_list()``, ``get_all()``, ``get_by_id()``,
``create()``, ``update()``, and ``delete()``. Read-only and specialized models
expose only operations supported by Kolleno's published API.
