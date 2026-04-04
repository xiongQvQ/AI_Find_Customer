from emailing.policy import choose_email_target, expand_email_targets


def test_choose_verified_decision_maker_first():
    lead = {
        "decision_makers": [
            {"name": "Owner", "title": "Owner", "email": "owner@acme.com"},
            {"name": "Buyer", "title": "Purchasing Manager", "email": "buyer@acme.com"},
        ],
        "emails": ["info@acme.com"],
    }
    target = choose_email_target(lead)
    assert target["target_email"] == "buyer@acme.com"
    assert target["target_type"] == "decision_maker_verified"


def test_choose_inferred_decision_maker_before_generic():
    lead = {
        "decision_makers": [
            {"name": "John Doe", "title": "Sales Director", "email": "john.doe@acme.com (inferred)"},
        ],
        "emails": ["info@acme.com"],
    }
    target = choose_email_target(lead)
    assert target["target_email"] == "john.doe@acme.com"
    assert target["target_type"] == "decision_maker_inferred_from_pattern"


def test_falls_back_to_generic_company_email():
    lead = {
        "decision_makers": [],
        "emails": ["info@acme.com", "contact@acme.com"],
    }
    target = choose_email_target(lead)
    assert target["target_email"] == "contact@acme.com" or target["target_email"] == "info@acme.com"
    assert target["target_type"] == "generic_company_email"


def test_returns_none_when_no_email_available():
    target = choose_email_target({"decision_makers": [], "emails": []})
    assert target["target_type"] == "none"
    assert target["target_email"] == ""


def test_expand_email_targets_keeps_all_unique_business_emails():
    lead = {
        "decision_makers": [
            {"name": "Buyer", "title": "Purchasing Manager", "email": "buyer@acme.com"},
            {"name": "Owner", "title": "Owner", "email": "owner@acme.com"},
        ],
        "emails": ["info@acme.com", "sales@acme.com", "buyer@acme.com"],
    }
    targets = expand_email_targets(lead)
    assert [item["target_email"] for item in targets] == [
        "buyer@acme.com",
        "owner@acme.com",
        "info@acme.com",
        "sales@acme.com",
    ]
