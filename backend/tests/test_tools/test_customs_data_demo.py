"""Tests for scripts/customs_data_demo.py signal extraction and summarization."""

from scripts.customs_data_demo import (
    build_customs_queries,
    extract_signal_from_result,
    summarize_signals,
)


def test_build_customs_queries_contains_core_patterns():
    queries = build_customs_queries(
        "Acme GmbH",
        country="Germany",
        product_keywords=["micro switch", "rotary switch"],
    )
    assert any('"Acme GmbH" customs data' in q for q in queries)
    assert any('"Acme GmbH" Germany import export' in q for q in queries)
    assert any("site:panjiva.com" in q for q in queries)


def test_extract_signal_from_result_with_concrete_trade_facts():
    row = {
        "title": "Acme GmbH Import Export Data 2024 | Panjiva",
        "link": "https://panjiva.com/Acme-GmbH/12345",
        "snippet": "Acme GmbH import shipments from China and Turkey in 2024. HS code 853650."
    }
    sig = extract_signal_from_result(row, company_name="Acme GmbH", product_keywords=["micro switch"], country_hint="Germany")

    assert sig is not None
    assert sig.trade_direction in ("import", "import_export")
    assert sig.period in ("2024", "2024-2024")
    assert "China" in sig.partner_countries
    assert "853650" in sig.hs_codes
    assert sig.confidence >= 0.6


def test_extract_signal_returns_none_without_trade_keywords():
    row = {
        "title": "Acme company profile",
        "link": "https://example.com/acme",
        "snippet": "About us and team introduction"
    }
    assert extract_signal_from_result(row, company_name="Acme GmbH", product_keywords=["micro switch"]) is None


def test_extract_signal_filters_non_target_company_noise():
    row = {
        "title": "Tung Nguyen Transport J S C Import Export Turnover",
        "link": "https://www.exportgenius.in/company/tung-nguyen",
        "snippet": "Import shipments from Vietnam 2024 HS code 853650",
    }
    assert extract_signal_from_result(row, company_name="Acme GmbH", product_keywords=["micro switch"]) is None


def test_extract_signal_filters_generic_directory_pages():
    row = {
        "title": "Companies - Chemicals - Hamburg, Germany - Importers / Exporters",
        "link": "https://www.tradeholding.net/default.cgi/action/viewcompanies/maincatid/06/classification/Chemicals/inlocationid/08306/",
        "snippet": "Import export directory for Germany",
    }
    assert extract_signal_from_result(row, company_name="Acme GmbH", product_keywords=["micro switch"]) is None


def test_summarize_signals_no_data():
    out = summarize_signals([])
    assert out["status"] == "no_data"
    assert out["evidence"] == []
