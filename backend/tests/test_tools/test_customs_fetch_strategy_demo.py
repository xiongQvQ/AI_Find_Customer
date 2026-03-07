"""Tests for customs_fetch_strategy_demo helpers."""

from scripts.customs_fetch_strategy_demo import analyze_text


def test_analyze_text_detects_trade_signals():
    text = (
        "Acme GmbH import shipments from China in 2024. "
        "HS code 853650. Customs trade data shows consignee records."
    )
    result = analyze_text(text, company_name="Acme GmbH")

    assert result["trade_term_count"] >= 3
    assert "2024" in result["years_found"]
    assert "853650" in result["hs_codes_found"]
    assert "acme" in result["company_token_hits"]
    assert result["has_structured_trade_signal"] is True


def test_analyze_text_handles_plain_content():
    result = analyze_text("Simple homepage with no trade content.", company_name="Acme GmbH")
    assert result["trade_term_count"] == 0
    assert result["has_structured_trade_signal"] is False
