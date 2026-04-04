from __future__ import annotations

import json

from scripts.headless_worker import _headers, _normalize_base_url, build_hunt_payload, run_cycle


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


def test_run_cycle_creates_hunt_then_campaign(monkeypatch):
    class Args(_Args):
        api_base_url = "http://127.0.0.1:8000"
        api_token = "secret"
        request_timeout_seconds = 30
        status_poll_seconds = 0
        auto_start_campaign = True
        campaign_name_prefix = "Auto Campaign"

    responses = [
        {"template_seed": {"source": "pre_generated", "template_profile": {}, "template_plan": {}}},
        {"hunt_id": "hunt-123"},
        {"status": "running", "current_stage": "search", "leads_count": 40, "email_sequences_count": 0},
        {"status": "completed", "current_stage": "email_craft", "leads_count": 100, "email_sequences_count": 12},
        {"status": "completed", "leads": [{"company_name": "Acme"}], "email_sequences": [{} for _ in range(12)]},
        {"campaign_id": "camp-456", "sequence_count": 12},
        {"campaign_id": "camp-456", "status": "active"},
    ]
    calls: list[tuple[str, str]] = []

    def fake_request_json(*, method, base_url, path, api_token, payload=None, timeout_seconds=60):
        calls.append((method, path))
        return responses.pop(0)

    monkeypatch.setattr("scripts.headless_worker._request_json", fake_request_json)
    monkeypatch.setattr("scripts.headless_worker.time.sleep", lambda _: None)
    monkeypatch.setattr("scripts.headless_worker._notify_feishu", lambda text: None)

    result = run_cycle(Args())

    assert result["hunt_id"] == "hunt-123"
    assert result["lead_count"] == 1
    assert result["email_sequence_count"] == 12
    assert result["campaign"] == {"campaign_id": "camp-456", "status": "active"}
    assert calls == [
        ("POST", "/api/v1/email-template-seeds/prepare"),
        ("POST", "/api/v1/hunts"),
        ("GET", "/api/v1/hunts/hunt-123/status"),
        ("GET", "/api/v1/hunts/hunt-123/status"),
        ("GET", "/api/v1/hunts/hunt-123/result"),
        ("POST", "/api/v1/hunts/hunt-123/email-campaigns"),
        ("POST", "/api/v1/email-campaigns/camp-456/start"),
    ]


def test_run_cycle_skips_campaign_when_disabled(monkeypatch):
    class Args(_Args):
        api_base_url = "http://127.0.0.1:8000"
        api_token = ""
        request_timeout_seconds = 30
        status_poll_seconds = 0
        auto_start_campaign = False
        campaign_name_prefix = "Auto Campaign"

    responses = [
        {"template_seed": {"source": "pre_generated", "template_profile": {}, "template_plan": {}}},
        {"hunt_id": "hunt-xyz"},
        {"status": "completed", "current_stage": "email_craft", "leads_count": 100, "email_sequences_count": 3},
        {"status": "completed", "leads": [{"company_name": "Acme"}], "email_sequences": [{}]},
    ]

    def fake_request_json(*, method, base_url, path, api_token, payload=None, timeout_seconds=60):
        return responses.pop(0)

    monkeypatch.setattr("scripts.headless_worker._request_json", fake_request_json)
    monkeypatch.setattr("scripts.headless_worker._notify_feishu", lambda text: None)

    result = run_cycle(Args())

    assert result["hunt_id"] == "hunt-xyz"
    assert result["campaign"] is None
