from fastapi.testclient import TestClient

from api.app import create_app


def test_create_and_start_email_campaign(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    hunt = {
        "status": "completed",
        "result": {
            "email_sequences": [
                {
                    "lead": {"company_name": "Acme", "website": "https://acme.com"},
                    "locale": "en_US",
                    "review_summary": {"status": "approved", "score": 92},
                    "auto_send_eligible": True,
                    "generation_mode": "template_pool",
                    "template_id": "tpl_123",
                    "template_group": "en_US|decision_maker_verified|general",
                    "template_usage_index": 1,
                    "template_max_send_count": 100,
                    "target": {
                        "target_email": "buyer@acme.com",
                        "target_name": "Jane",
                        "target_title": "Purchasing Manager",
                        "target_type": "decision_maker_verified",
                    },
                    "emails": [
                        {"sequence_number": 1, "email_type": "company_intro", "subject": "Hi", "body_text": "A", "suggested_send_day": 0},
                        {"sequence_number": 2, "email_type": "product_showcase", "subject": "Hi2", "body_text": "B", "suggested_send_day": 3},
                        {"sequence_number": 3, "email_type": "partnership_proposal", "subject": "Hi3", "body_text": "C", "suggested_send_day": 7},
                    ],
                }
            ]
        },
    }
    saved = {}

    monkeypatch.setattr("api.email_routes.load_hunt", lambda hunt_id: hunt)
    monkeypatch.setattr("api.email_routes.save_hunt", lambda hunt_id, data: saved.update({hunt_id: data}))
    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_provider_type": "smtp",
        "email_from_name": "B2Binsights",
        "email_from_address": "sales@example.com",
        "email_reply_to": "sales@example.com",
        "email_smtp_host": "smtp.example.com",
        "email_smtp_port": 587,
        "email_smtp_username": "sales@example.com",
        "email_smtp_password": "secret",
        "email_smtp_last_test_at": "2026-04-04T10:00:00Z",
        "email_imap_host": "",
        "email_imap_port": 993,
        "email_imap_username": "",
        "email_imap_password": "",
        "email_use_tls": True,
        "email_daily_send_limit": 50,
        "email_hourly_send_limit": 10,
        "email_language_mode": "auto_by_region",
        "email_default_language": "en",
        "email_fallback_language": "en",
        "email_tone": "professional",
        "email_step1_delay_days": 0,
        "email_step2_delay_days": 3,
        "email_step3_delay_days": 3,
        "email_min_fit_score_to_send": 0.6,
        "email_min_contactability_score_to_send": 0.45,
    })())

    res = client.post("/api/v1/hunts/hunt_1/email-campaigns", json={"name": "Test Campaign"})
    assert res.status_code == 200
    campaign_id = res.json()["campaign_id"]

    res = client.post(f"/api/v1/email-campaigns/{campaign_id}/start")
    assert res.status_code == 200
    assert res.json()["status"] == "active"

    res = client.get("/api/v1/hunts/hunt_1/email-campaigns")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["template_summary"][0]["template_id"] == "tpl_123"
    assert saved["hunt_1"]["result"]["email_campaign_summary"]["template_summary"][0]["template_id"] == "tpl_123"


def test_create_campaign_skips_blocked_template(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    hunt = {
        "status": "completed",
        "result": {
            "email_sequences": [
                {
                    "lead": {"company_name": "Blocked", "website": "https://blocked.com"},
                    "locale": "en_US",
                    "generation_mode": "template_pool",
                    "template_id": "tpl_bad",
                    "template_group": "en_US|decision_maker_verified|general",
                    "template_usage_index": 1,
                    "template_max_send_count": 100,
                    "template_performance": {"status": "underperforming"},
                    "target": {
                        "target_email": "buyer@blocked.com",
                        "target_name": "Jane",
                        "target_title": "Purchasing Manager",
                        "target_type": "decision_maker_verified",
                    },
                    "emails": [
                        {"sequence_number": 1, "email_type": "company_intro", "subject": "Hi", "body_text": "A", "suggested_send_day": 0},
                    ],
                }
            ]
        },
    }

    monkeypatch.setattr("api.email_routes.load_hunt", lambda hunt_id: hunt)
    monkeypatch.setattr("api.email_routes.save_hunt", lambda hunt_id, data: None)
    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_provider_type": "smtp",
        "email_from_name": "B2Binsights",
        "email_from_address": "sales@example.com",
        "email_reply_to": "sales@example.com",
        "email_smtp_host": "smtp.example.com",
        "email_smtp_port": 587,
        "email_smtp_username": "sales@example.com",
        "email_smtp_password": "secret",
        "email_smtp_last_test_at": "2026-04-04T10:00:00Z",
        "email_imap_host": "",
        "email_imap_port": 993,
        "email_imap_username": "",
        "email_imap_password": "",
        "email_use_tls": True,
        "email_daily_send_limit": 50,
        "email_hourly_send_limit": 10,
        "email_language_mode": "auto_by_region",
        "email_default_language": "en",
        "email_fallback_language": "en",
        "email_tone": "professional",
        "email_step1_delay_days": 0,
        "email_step2_delay_days": 3,
        "email_step3_delay_days": 3,
        "email_min_fit_score_to_send": 0.6,
        "email_min_contactability_score_to_send": 0.45,
    })())

    res = client.post("/api/v1/hunts/hunt_1/email-campaigns", json={"name": "Blocked Campaign"})
    assert res.status_code == 200
    assert res.json()["sequence_count"] == 0


def test_create_campaign_skips_unapproved_sequences(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    hunt = {
        "status": "completed",
        "result": {
            "email_sequences": [
                {
                    "lead": {"company_name": "Needs Review", "website": "https://review.com"},
                    "locale": "en_US",
                    "review_summary": {"status": "needs_review", "score": 61},
                    "auto_send_eligible": False,
                    "target": {
                        "target_email": "buyer@review.com",
                        "target_name": "Jane",
                        "target_title": "Purchasing Manager",
                        "target_type": "decision_maker_verified",
                    },
                    "emails": [
                        {"sequence_number": 1, "email_type": "company_intro", "subject": "Hi", "body_text": "A", "suggested_send_day": 0},
                    ],
                },
                {
                    "lead": {"company_name": "Approved", "website": "https://approved.com"},
                    "locale": "en_US",
                    "review_summary": {"status": "approved", "score": 90},
                    "auto_send_eligible": True,
                    "target": {
                        "target_email": "buyer@approved.com",
                        "target_name": "John",
                        "target_title": "Purchasing Manager",
                        "target_type": "decision_maker_verified",
                    },
                    "emails": [
                        {"sequence_number": 1, "email_type": "company_intro", "subject": "Hi", "body_text": "A", "suggested_send_day": 0},
                    ],
                }
            ]
        },
    }

    monkeypatch.setattr("api.email_routes.load_hunt", lambda hunt_id: hunt)
    monkeypatch.setattr("api.email_routes.save_hunt", lambda hunt_id, data: None)
    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_provider_type": "smtp",
        "email_from_name": "B2Binsights",
        "email_from_address": "sales@example.com",
        "email_reply_to": "sales@example.com",
        "email_smtp_host": "smtp.example.com",
        "email_smtp_port": 587,
        "email_smtp_username": "sales@example.com",
        "email_smtp_password": "secret",
        "email_smtp_last_test_at": "2026-04-04T10:00:00Z",
        "email_imap_host": "",
        "email_imap_port": 993,
        "email_imap_username": "",
        "email_imap_password": "",
        "email_use_tls": True,
        "email_daily_send_limit": 50,
        "email_hourly_send_limit": 10,
        "email_language_mode": "auto_by_region",
        "email_default_language": "en",
        "email_fallback_language": "en",
        "email_tone": "professional",
        "email_step1_delay_days": 0,
        "email_step2_delay_days": 3,
        "email_step3_delay_days": 3,
        "email_min_fit_score_to_send": 0.6,
        "email_min_contactability_score_to_send": 0.45,
    })())

    res = client.post("/api/v1/hunts/hunt_1/email-campaigns", json={"name": "Approved Only"})
    assert res.status_code == 200
    assert res.json()["sequence_count"] == 1


def test_run_email_scheduler_route(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_from_address": "sales@example.com",
        "email_smtp_host": "smtp.example.com",
        "email_smtp_port": 587,
        "email_smtp_username": "sales@example.com",
        "email_smtp_password": "secret",
        "email_smtp_last_test_at": "2026-04-04T10:00:00Z",
    })())

    called = {}

    async def fake_run_scheduler_once(store):
        called["db_path"] = store.db_path
        return {"sent": 1, "failed": 0, "skipped": 2}

    monkeypatch.setattr("api.email_routes.run_scheduler_once", fake_run_scheduler_once)

    res = client.post("/api/v1/email-scheduler/run")
    assert res.status_code == 200
    assert res.json() == {"sent": 1, "failed": 0, "skipped": 2}
    assert called["db_path"] == str(tmp_path / "email.db")


def test_run_email_reply_check_route(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_provider_type": "smtp",
        "email_from_name": "B2Binsights",
        "email_from_address": "sales@example.com",
        "email_reply_to": "sales@example.com",
        "email_smtp_host": "smtp.example.com",
        "email_smtp_port": 587,
        "email_smtp_username": "sales@example.com",
        "email_smtp_password": "secret",
        "email_imap_host": "imap.example.com",
        "email_imap_port": 993,
        "email_imap_username": "sales@example.com",
        "email_imap_password": "imap-secret",
        "email_imap_last_test_at": "2026-04-04T10:00:00Z",
        "email_use_tls": True,
        "email_daily_send_limit": 50,
        "email_hourly_send_limit": 10,
    })())

    called = {}

    async def fake_run_reply_detection_once(store, account):
        called["db_path"] = store.db_path
        called["account_id"] = account["id"]
        return {"checked": 3, "matched": 1, "skipped": 2, "ignored": 1}

    monkeypatch.setattr("api.email_routes.run_reply_detection_once", fake_run_reply_detection_once)

    res = client.post("/api/v1/email-replies/check")
    assert res.status_code == 200
    assert res.json() == {"checked": 3, "matched": 1, "skipped": 2, "ignored": 1}
    assert called == {"db_path": str(tmp_path / "email.db"), "account_id": "default"}


def test_create_campaign_requires_smtp_configuration(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    hunt = {
        "status": "completed",
        "result": {
            "email_sequences": [
                {
                    "lead": {"company_name": "Acme", "website": "https://acme.com"},
                    "locale": "en_US",
                    "target": {
                        "target_email": "buyer@acme.com",
                        "target_name": "Jane",
                        "target_title": "Purchasing Manager",
                        "target_type": "decision_maker_verified",
                    },
                    "emails": [
                        {"sequence_number": 1, "email_type": "company_intro", "subject": "Hi", "body_text": "A", "suggested_send_day": 0},
                    ],
                }
            ]
        },
    }

    monkeypatch.setattr("api.email_routes.load_hunt", lambda hunt_id: hunt)
    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_provider_type": "smtp",
        "email_from_name": "B2Binsights",
        "email_from_address": "",
        "email_reply_to": "",
        "email_smtp_host": "",
        "email_smtp_port": 0,
        "email_smtp_username": "",
        "email_smtp_password": "",
        "email_imap_host": "",
        "email_imap_port": 993,
        "email_imap_username": "",
        "email_imap_password": "",
        "email_use_tls": True,
        "email_daily_send_limit": 50,
        "email_hourly_send_limit": 10,
        "email_language_mode": "auto_by_region",
        "email_default_language": "en",
        "email_fallback_language": "en",
        "email_tone": "professional",
        "email_step1_delay_days": 0,
        "email_step2_delay_days": 3,
        "email_step3_delay_days": 3,
        "email_min_fit_score_to_send": 0.6,
        "email_min_contactability_score_to_send": 0.45,
    })())

    res = client.post("/api/v1/hunts/hunt_1/email-campaigns", json={"name": "Blocked Campaign"})
    assert res.status_code == 409
    assert "SMTP is not configured" in res.json()["detail"]


def test_start_campaign_requires_smtp_configuration(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_from_address": "",
        "email_smtp_host": "",
        "email_smtp_port": 0,
        "email_smtp_username": "",
        "email_smtp_password": "",
    })())

    from emailing.store import EmailStore

    store = EmailStore(str(tmp_path / "email.db"))
    store.init_db()
    store.create_campaign({
        "id": "cmp_1",
        "hunt_id": "hunt_1",
        "email_account_id": "default",
        "name": "Test",
        "status": "draft",
        "language_mode": "auto_by_region",
        "default_language": "en",
        "fallback_language": "en",
        "tone": "professional",
        "step1_delay_days": 0,
        "step2_delay_days": 3,
        "step3_delay_days": 3,
        "min_fit_score": 0.6,
        "min_contactability_score": 0.45,
        "created_at": "2026-04-04T00:00:00Z",
        "updated_at": "2026-04-04T00:00:00Z",
    })

    res = client.post("/api/v1/email-campaigns/cmp_1/start")
    assert res.status_code == 409
    assert "SMTP is not configured" in res.json()["detail"]


def test_start_campaign_requires_smtp_test_success(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_from_address": "sales@example.com",
        "email_smtp_host": "smtp.example.com",
        "email_smtp_port": 587,
        "email_smtp_username": "sales@example.com",
        "email_smtp_password": "secret",
        "email_smtp_last_test_at": "",
    })())

    from emailing.store import EmailStore

    store = EmailStore(str(tmp_path / "email.db"))
    store.init_db()
    store.create_campaign({
        "id": "cmp_2",
        "hunt_id": "hunt_1",
        "email_account_id": "default",
        "name": "Test",
        "status": "draft",
        "language_mode": "auto_by_region",
        "default_language": "en",
        "fallback_language": "en",
        "tone": "professional",
        "step1_delay_days": 0,
        "step2_delay_days": 3,
        "step3_delay_days": 3,
        "min_fit_score": 0.6,
        "min_contactability_score": 0.45,
        "created_at": "2026-04-04T00:00:00Z",
        "updated_at": "2026-04-04T00:00:00Z",
    })

    res = client.post("/api/v1/email-campaigns/cmp_2/start")
    assert res.status_code == 409
    assert "Please test SMTP in Settings" in res.json()["detail"]


def test_run_email_scheduler_requires_smtp_configuration(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_from_address": "",
        "email_smtp_host": "",
        "email_smtp_port": 0,
        "email_smtp_username": "",
        "email_smtp_password": "",
    })())

    res = client.post("/api/v1/email-scheduler/run")
    assert res.status_code == 409
    assert "SMTP is not configured" in res.json()["detail"]


def test_run_email_scheduler_requires_smtp_test_success(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_from_address": "sales@example.com",
        "email_smtp_host": "smtp.example.com",
        "email_smtp_port": 587,
        "email_smtp_username": "sales@example.com",
        "email_smtp_password": "secret",
        "email_smtp_last_test_at": "",
    })())

    res = client.post("/api/v1/email-scheduler/run")
    assert res.status_code == 409
    assert "Please test SMTP in Settings" in res.json()["detail"]


def test_run_email_reply_check_requires_imap_configuration(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_imap_host": "",
        "email_imap_port": 0,
        "email_imap_username": "",
        "email_imap_password": "",
    })())

    res = client.post("/api/v1/email-replies/check")
    assert res.status_code == 409
    assert "IMAP is not configured" in res.json()["detail"]


def test_run_email_reply_check_requires_imap_test_success(monkeypatch, tmp_path):
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_imap_host": "imap.example.com",
        "email_imap_port": 993,
        "email_imap_username": "sales@example.com",
        "email_imap_password": "secret",
        "email_imap_last_test_at": "",
    })())

    res = client.post("/api/v1/email-replies/check")
    assert res.status_code == 409
    assert "Please test IMAP in Settings" in res.json()["detail"]


def test_email_routes_require_token_when_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("API_ACCESS_TOKEN", "secret-token")
    from config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr("api.email_routes.get_settings", lambda: type("S", (), {
        "email_db_path": str(tmp_path / "email.db"),
        "email_provider_type": "smtp",
        "email_from_name": "B2Binsights",
        "email_from_address": "sales@example.com",
        "email_reply_to": "sales@example.com",
        "email_smtp_host": "smtp.example.com",
        "email_smtp_port": 587,
        "email_smtp_username": "sales@example.com",
        "email_smtp_password": "secret",
        "email_smtp_last_test_at": "2026-04-04T10:00:00Z",
        "email_imap_host": "",
        "email_imap_port": 993,
        "email_imap_username": "",
        "email_imap_password": "",
        "email_use_tls": True,
        "email_daily_send_limit": 50,
        "email_hourly_send_limit": 10,
        "api_access_token": "secret-token",
    })())

    unauthorized = client.post("/api/v1/email-scheduler/run")
    authorized = client.post("/api/v1/email-scheduler/run", headers={"X-API-Key": "secret-token"})

    get_settings.cache_clear()
    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
