from emailing.body_format import format_plaintext_email_body


def test_format_plaintext_email_body_adds_paragraph_breaks():
    raw = (
        "Dear Sir/Madam, I noticed Denney Electric Supply serves contractors and industrial customers with electrical "
        "components in the Pennsylvania area. We are Guangdong Yushun Electrical Co., Ltd., a specialized manufacturer "
        "of micro switches, rotary selectors, and toggle switches with over 10 years of experience. Given your focus on "
        "supplying reliable electrical components to local contractors, there may be a natural fit. If this product "
        "category is of interest, I would be happy to share an overview of the relevant models and certifications. "
        "Kind regards,"
    )

    formatted = format_plaintext_email_body(raw)

    assert "\n\n" in formatted
    assert "Kind regards," in formatted.split("\n\n")[-1]


def test_format_plaintext_email_body_keeps_existing_paragraphs():
    raw = "Dear Sir/Madam,\n\nWe manufacture micro switches for industrial controls.\n\nKind regards,"

    assert format_plaintext_email_body(raw) == raw
