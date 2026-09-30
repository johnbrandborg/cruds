from pathlib import Path
from unittest.mock import Mock, call

import pytest

from cruds import Client
from cruds.interfaces.kolleno import Kolleno  # ty: ignore[unresolved-import]


DOMAIN_NAME = "https://api.example.test/v1/"
DEFAULT_DOMAIN_NAME = "https://api.kolleno.com/v1/"
CLIENT_ID = "client-id"
CLIENT_SECRET = "client-secret"


@pytest.fixture
def kolleno():
    return Kolleno(DOMAIN_NAME, CLIENT_ID, CLIENT_SECRET)


def test_Kolleno_initializes_client_and_api_authentication(kolleno):
    assert isinstance(kolleno.client, Client)
    assert kolleno.client.host == DOMAIN_NAME
    assert (
        kolleno.client.request_headers["Authorization"] == "API client-id:client-secret"
    )


def test_Kolleno_uses_default_domain_name():
    kolleno = Kolleno(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    assert kolleno.client.host == DEFAULT_DOMAIN_NAME


def test_Kolleno_passes_transport_options_to_client():
    kolleno = Kolleno(
        DOMAIN_NAME,
        CLIENT_ID,
        CLIENT_SECRET,
        raise_status=False,
        serialize=False,
    )

    assert kolleno.client.raise_status is False
    assert kolleno.client.serialize is False


@pytest.mark.parametrize(
    ("domain_name", "client_id", "client_secret"),
    [
        ("", CLIENT_ID, CLIENT_SECRET),
        (DOMAIN_NAME, "", CLIENT_SECRET),
        (DOMAIN_NAME, CLIENT_ID, ""),
        (DOMAIN_NAME, "invalid\nid", CLIENT_SECRET),
        (DOMAIN_NAME, CLIENT_ID, "invalid\rsecret"),
    ],
)
def test_Kolleno_rejects_invalid_configuration(domain_name, client_id, client_secret):
    with pytest.raises(ValueError):
        Kolleno(domain_name, client_id, client_secret)


def test_Kolleno_models_are_isolated_between_clients():
    first = Kolleno(DOMAIN_NAME, "first", CLIENT_SECRET)
    second = Kolleno(DOMAIN_NAME, "second", CLIENT_SECRET)

    assert first.customer is not second.customer
    assert first.customer._owner is first
    assert second.customer._owner is second


@pytest.mark.parametrize(
    ("model_name", "uri"),
    [
        ("company", "company"),
        ("card_detail", "card-detail"),
        ("direct_debit_detail", "direct-debit-detail"),
        ("customer", "customer"),
        ("customer_portal", "customer/portal-url"),
        ("customer_custom_fields", "customer/custom-fields"),
        ("credit_note", "credit-note"),
        ("credit_note_pdf", "credit-note/pdf"),
        ("invoice", "invoice"),
        ("invoice_custom_fields", "invoice/custom-fields"),
        ("invoice_pdf", "invoice-pdf"),
        ("invoice_pdf_download", "invoice/pdf"),
        ("match", "match"),
        ("person", "person/company"),
        ("person_invoice", "person-invoice"),
        ("position_external", "position-external"),
        ("report_file", "report-file"),
        ("tag", "tag"),
        ("tag_category", "tag/category"),
        ("transaction", "transaction"),
        ("timeline", "step"),
    ],
)
def test_Kolleno_exposes_documented_models(kolleno, model_name, uri):
    assert getattr(kolleno, model_name)._uri == uri


def test_Kolleno_get_list_builds_hierarchical_path_and_filters(kolleno):
    kolleno.client.read = Mock(return_value={"results": []})

    response = kolleno.customer.get_list(
        "company/id",
        limit=5,
        offset=10,
        fields="source_id,balance",
    )

    assert response == {"results": []}
    kolleno.client.read.assert_called_once_with(
        "customer/company%2Fid/",
        params={"limit": 5, "offset": 10, "fields": "source_id,balance"},
    )


def test_Kolleno_get_by_id_uses_all_resource_identifiers(kolleno):
    kolleno.client.read = Mock(return_value={"id": "customer-id"})

    kolleno.customer.get_by_id("company-id", "customer-id")

    kolleno.client.read.assert_called_once_with(
        "customer/company-id/customer-id/",
        params=None,
    )


def test_Kolleno_create_update_and_delete(kolleno):
    kolleno.client.create = Mock(return_value={"id": "customer-id"})
    kolleno.client.update = Mock(return_value={"id": "customer-id"})
    kolleno.client.delete = Mock(return_value=b"")

    created = kolleno.customer.create("company-id", data={"name": "Example"})
    updated = kolleno.customer.update(
        "company-id",
        "customer-id",
        data={"warning_level": "high"},
    )
    deleted = kolleno.customer.delete("company-id", "customer-id")

    assert created == {"id": "customer-id"}
    assert updated == {"id": "customer-id"}
    assert deleted == b""
    kolleno.client.create.assert_called_once_with(
        "customer/company-id/",
        data={"name": "Example"},
        params=None,
        files=None,
    )
    kolleno.client.update.assert_called_once_with(
        "customer/company-id/customer-id/",
        data={"warning_level": "high"},
        params=None,
        files=None,
    )
    kolleno.client.delete.assert_called_once_with(
        "customer/company-id/customer-id/",
        params=None,
    )


def test_Kolleno_invoice_pdf_supports_multipart_upload(kolleno):
    kolleno.client.create = Mock(return_value={"id": "pdf-id"})
    files = {"file": ("invoice.pdf", b"pdf", "application/pdf")}

    kolleno.invoice_pdf.create("invoice-id", data={}, files=files)

    kolleno.client.create.assert_called_once_with(
        "invoice-pdf/invoice-id/",
        data={},
        params=None,
        files=files,
    )


def test_Kolleno_download_uses_client_download(kolleno, tmp_path):
    output = tmp_path / "invoice.pdf"
    kolleno.client.download = Mock(return_value=output)

    result = kolleno.invoice_pdf_download.download(
        "company-id",
        "invoice-id",
        path=tmp_path,
        filename="invoice.pdf",
    )

    assert result == Path(output)
    kolleno.client.download.assert_called_once_with(
        "invoice/pdf/company-id/invoice-id/",
        path=tmp_path,
        filename="invoice.pdf",
        params=None,
    )


def test_Kolleno_customer_portal_uses_customer_query_parameter(kolleno):
    kolleno.client.read = Mock(return_value={"customer_portal_url": "https://portal"})

    kolleno.customer_portal.get_list("company-id", customer="customer-id")

    kolleno.client.read.assert_called_once_with(
        "customer/portal-url/company-id/",
        params={"customer": "customer-id"},
    )


def test_Kolleno_get_all_yields_paginated_results(kolleno):
    kolleno.client.read = Mock(
        side_effect=[
            {
                "count": 3,
                "next": "https://api.example.test/v1/company/?limit=2&offset=2",
                "previous": None,
                "results": [{"id": "1"}, {"id": "2"}],
            },
            {
                "count": 3,
                "next": None,
                "previous": "https://api.example.test/v1/company/?limit=2&offset=0",
                "results": [{"id": "3"}],
            },
        ]
    )

    results = list(kolleno.company.get_all(limit=2))

    assert results == [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    assert kolleno.client.read.call_args_list == [
        call("company/", params={"limit": 2, "offset": 0}),
        call("company/", params={"limit": 2, "offset": 2}),
    ]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"limit": 0}, "limit"),
        ({"limit": 1.5}, "limit"),
        ({"offset": -1}, "offset"),
    ],
)
def test_Kolleno_get_all_validates_pagination(kolleno, kwargs, message):
    with pytest.raises(ValueError, match=message):
        list(kolleno.company.get_all(**kwargs))


@pytest.mark.parametrize(
    "response",
    [
        b"not-json",
        {"count": 1, "next": None},
        {"count": 1, "next": None, "results": {}},
    ],
)
def test_Kolleno_get_all_rejects_invalid_responses(kolleno, response):
    kolleno.client.read = Mock(return_value=response)

    with pytest.raises(TypeError):
        list(kolleno.company.get_all())


def test_Kolleno_rejects_empty_path_components(kolleno):
    with pytest.raises(ValueError, match="cannot be empty"):
        kolleno.customer.get_by_id("company-id", "")
