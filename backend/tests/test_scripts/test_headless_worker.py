from __future__ import annotations

import json

from scripts.headless_worker import _headers, _normalize_base_url, build_hunt_payload


class _Args:
    payload_file = ""
    website_url = None
    description = "Find electrical distributors"
    product_keywords = ["micro switch"]
    target_customer_profile = "Distributors"
    target_regions = ["United States"]
    target_lead_count = 100
    max_rounds = 8
    min_new_leads_threshold = 5
    enable_email_craft = True
    email_template_examples = []
    email_template_notes = "Keep it concise"


def test_headers_add_api_key_only_when_present():
    assert _headers("") == {"Content-Type": "application/json"}
    assert _headers("secret") == {
        "Content-Type": "application/json",
        "X-API-Key": "secret",
    }


def test_normalize_base_url_strips_trailing_slash():
    assert _normalize_base_url("http://127.0.0.1:8000/") == "http://127.0.0.1:8000"


def test_build_hunt_payload_uses_args():
    payload = build_hunt_payload(_Args())
    assert payload["description"] == "Find electrical distributors"
    assert payload["product_keywords"] == ["micro switch"]
    assert payload["target_regions"] == ["United States"]
    assert payload["target_lead_count"] == 100
    assert payload["enable_email_craft"] is True


def test_build_hunt_payload_merges_payload_file(tmp_path):
    job_path = tmp_path / "job.json"
    job_path.write_text(
        json.dumps(
            {
                "description": "Find buyers in Germany",
                "product_keywords": ["toggle switch"],
                "target_lead_count": 55,
                "enable_email_craft": False,
            }
        ),
        encoding="utf-8",
    )

    class Args(_Args):
        payload_file = str(job_path)
        description = None
        product_keywords = []
        target_lead_count = None
        enable_email_craft = None

    payload = build_hunt_payload(Args())
    assert payload["description"] == "Find buyers in Germany"
    assert payload["product_keywords"] == ["toggle switch"]
    assert payload["target_lead_count"] == 55
    assert payload["enable_email_craft"] is False
