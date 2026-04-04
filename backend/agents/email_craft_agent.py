"""EmailCraftAgent — concurrent 3-email sequence generation per lead, multi-language.

Uses a ReAct loop (Think → Draft → Validate → Revise) with max 3 iterations.
The validate_emails tool checks language correctness, formality, salutation format,
and cultural norms per locale before the agent finalises the output.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from config.settings import get_settings
from emailing.template_pipeline import compose_template_plan, extract_template_profile
from graph.state import HuntState
from tools.llm_client import LLMTool
from tools.react_runner import ToolDef, react_loop

logger = logging.getLogger(__name__)

# ── Locale rules: validation criteria per language ────────────────────────────
_LOCALE_RULES: dict[str, dict[str, Any]] = {
    "de": {
        "language": "German", "formality": "formal", "script": "latin",
        "salutation": "Sehr geehrte(r) Damen und Herren / Sehr geehrte(r) [Name]",
        "closing": "Mit freundlichen Grüßen",
        "checks": [
            "All text must be in German (no English sentences)",
            "Use formal 'Sie' (not 'du') throughout",
            "Subject line must be in German",
            "Use proper German umlauts: ä, ö, ü, ß",
        ],
    },
    "fr": {
        "language": "French", "formality": "formal", "script": "latin",
        "salutation": "Madame, Monsieur / Madame [Nom] / Monsieur [Nom]",
        "closing": "Veuillez agréer, Madame/Monsieur, l'expression de mes salutations distinguées",
        "checks": [
            "All text must be in French (no English sentences)",
            "Use formal 'vous' (not 'tu')",
            "Subject line must be in French",
            "Use proper French accents: é, è, ê, à, ç",
        ],
    },
    "es": {
        "language": "Spanish", "formality": "formal", "script": "latin",
        "salutation": "Estimado/a Sr./Sra. [Apellido] / A quien corresponda",
        "closing": "Atentamente / Un cordial saludo",
        "checks": [
            "All text must be in Spanish",
            "Use formal 'usted' (not 'tú')",
            "Subject line must be in Spanish",
            "Use proper Spanish punctuation: ¿?, ¡!",
        ],
    },
    "pt": {
        "language": "Portuguese", "formality": "formal", "script": "latin",
        "salutation": "Prezado(a) Sr./Sra. [Nome]",
        "closing": "Atenciosamente",
        "checks": [
            "All text must be in Portuguese",
            "pt_BR: Brazilian Portuguese is slightly less formal than European",
            "Subject line must be in Portuguese",
            "Use proper accents: ã, ç, ê, ó",
        ],
    },
    "it": {
        "language": "Italian", "formality": "formal", "script": "latin",
        "salutation": "Gentile Sig./Sig.ra [Cognome] / Spettabile [Azienda]",
        "closing": "Cordiali saluti / Distinti saluti",
        "checks": [
            "All text must be in Italian",
            "Use formal 'Lei' (not 'tu')",
            "Subject line must be in Italian",
        ],
    },
    "nl": {
        "language": "Dutch", "formality": "semi-formal", "script": "latin",
        "salutation": "Geachte heer/mevrouw [Naam] / Beste [Naam]",
        "closing": "Met vriendelijke groet",
        "checks": [
            "All text must be in Dutch",
            "Dutch business culture is direct; avoid flowery language",
            "Subject line must be in Dutch",
        ],
    },
    "pl": {
        "language": "Polish", "formality": "formal", "script": "latin",
        "salutation": "Szanowny Panie/Szanowna Pani [Nazwisko] / Szanowni Państwo",
        "closing": "Z poważaniem",
        "checks": [
            "All text must be in Polish",
            "Use formal address forms",
            "Subject line must be in Polish",
            "Use proper Polish characters: ą, ć, ę, ł, ń, ó, ś, ź, ż",
        ],
    },
    "ru": {
        "language": "Russian", "formality": "formal", "script": "cyrillic",
        "salutation": "Уважаемый/Уважаемая [Имя Отчество] / Уважаемые господа",
        "closing": "С уважением",
        "checks": [
            "All text must be in Russian using Cyrillic script",
            "Use formal address with name + patronymic if known",
            "Subject line must be in Russian",
        ],
    },
    "ja": {
        "language": "Japanese", "formality": "formal", "script": "japanese",
        "salutation": "株式会社[会社名] [部署] [役職] [氏名]様",
        "closing": "よろしくお願いいたします",
        "checks": [
            "All text must be in Japanese (kanji, hiragana, katakana as appropriate)",
            "Start with 'お世話になっております' for existing contacts",
            "Use keigo (敬語) — formal honorific language throughout",
            "Subject line must be in Japanese",
            "End with 以上、よろしくお願いいたします",
        ],
    },
    "ko": {
        "language": "Korean", "formality": "formal", "script": "hangul",
        "salutation": "[회사명] [직함] [성함] 귀중 / 안녕하십니까",
        "closing": "감사합니다 / 잘 부탁드립니다",
        "checks": [
            "All text must be in Korean (Hangul)",
            "Use formal speech level (합쇼체)",
            "Subject line must be in Korean",
        ],
    },
    "zh": {
        "language": "Chinese (Simplified)", "formality": "formal", "script": "chinese_simplified",
        "salutation": "尊敬的[姓名/职位]：/ 您好",
        "closing": "此致 敬礼 / 期待您的回复",
        "checks": [
            "All text must be in Simplified Chinese",
            "Use formal business Chinese (商务中文)",
            "Subject line must be in Chinese",
            "Use 贵公司 when referring to the recipient's company",
        ],
    },
    "tw": {
        "language": "Chinese (Traditional)", "formality": "formal", "script": "chinese_traditional",
        "salutation": "敬啟者 / 您好",
        "closing": "敬祝 商祺",
        "checks": [
            "All text must be in Traditional Chinese",
            "Use formal business Chinese",
            "Subject line must be in Traditional Chinese",
        ],
    },
    "ar": {
        "language": "Arabic", "formality": "formal", "script": "arabic",
        "salutation": "السيد/السيدة [الاسم] المحترم/المحترمة / تحية طيبة وبعد",
        "closing": "مع خالص التقدير والاحترام",
        "checks": [
            "All text must be in Arabic (right-to-left)",
            "Use Modern Standard Arabic (فصحى) for business",
            "Subject line must be in Arabic",
            "Open with Islamic greeting if appropriate: السلام عليكم",
        ],
    },
    "tr": {
        "language": "Turkish", "formality": "formal", "script": "latin",
        "salutation": "Sayın [Ad Soyad] / Sayın Yetkili",
        "closing": "Saygılarımla",
        "checks": [
            "All text must be in Turkish",
            "Use formal address 'Sayın'",
            "Subject line must be in Turkish",
            "Use proper Turkish characters: ç, ğ, ı, ö, ş, ü",
        ],
    },
    "en": {
        "language": "English", "formality": "professional", "script": "latin",
        "salutation": "Dear [Name] / Dear Sir/Madam",
        "closing": "Best regards / Kind regards",
        "checks": [
            "Professional business English",
            "Clear and concise sentences",
            "Subject line should be specific and compelling",
        ],
    },
}

# Country code → locale mapping
_COUNTRY_LOCALE_MAP = {
    "de": "de_DE", "at": "de_AT", "ch": "de_CH",
    "fr": "fr_FR", "be": "fr_BE",
    "es": "es_ES", "mx": "es_MX",
    "pt": "pt_PT", "br": "pt_BR",
    "it": "it_IT",
    "nl": "nl_NL",
    "ja": "ja_JP", "jp": "ja_JP",
    "ko": "ko_KR", "kr": "ko_KR",
    "zh": "zh_CN", "cn": "zh_CN", "tw": "zh_TW",
    "ru": "ru_RU",
    "sa": "ar_SA", "ae": "ar_AE",
    "tr": "tr_TR",
    "pl": "pl_PL",
    "cz": "cs_CZ", "ro": "ro_RO", "hu": "hu_HU",
    "ua": "uk_UA",
    "se": "sv_SE", "no": "nb_NO", "dk": "da_DK", "fi": "fi_FI",
    "th": "th_TH", "vn": "vi_VN", "id": "id_ID",
    "in": "hi_IN", "gr": "el_GR",
}

# ── ReAct system prompt ───────────────────────────────────────────────────────
EMAIL_REACT_SYSTEM = """You are an expert B2B email copywriter specialising in international business communication.

Your task: write a 3-email outreach sequence for a potential buyer/distributor, then validate and refine it.

## Workflow (follow this order):
1. THINK — analyse the lead profile, locale, industry, and cultural context.
2. DRAFT — write all 3 emails.
3. VALIDATE — call validate_emails with your draft JSON to check language, formality, salutation, and cultural fit.
4. REVISE — if validation returns issues, fix them and call validate_emails again (max 2 validation rounds).
5. OUTPUT — once validation passes, output the final JSON.

## Final output MUST be this exact JSON structure:
{
  "locale": "<locale>",
  "emails": [
    {
      "sequence_number": 1,
      "email_type": "company_intro",
      "subject": "...",
      "body_text": "...",
      "suggested_send_day": 0,
      "personalization_points": ["..."],
      "cultural_adaptations": ["..."]
    },
    {
      "sequence_number": 2,
      "email_type": "product_showcase",
      "subject": "...",
      "body_text": "...",
      "suggested_send_day": 3,
      "personalization_points": ["..."],
      "cultural_adaptations": ["..."]
    },
    {
      "sequence_number": 3,
      "email_type": "partnership_proposal",
      "subject": "...",
      "body_text": "...",
      "suggested_send_day": 7,
      "personalization_points": ["..."],
      "cultural_adaptations": ["..."]
    }
  ]
}

## Rules:
1. Write ALL subject and body_text in the target locale language.
2. Adapt tone, formality, salutation, and closing to the target culture.
3. Each email: 100-200 words.
4. Personalise based on the lead's industry and description.
5. Include specific product references.
6. Output ONLY the JSON object — no extra text."""


def _get_locale(country_code: str) -> str:
    """Map country code to locale. Default to en_US."""
    return _COUNTRY_LOCALE_MAP.get(country_code.lower(), "en_US")


def _get_locale_rules(locale: str) -> dict[str, Any]:
    """Get validation rules for a locale. Falls back to English rules."""
    parts = locale.lower().split("_")
    lang = parts[0]
    country = parts[1] if len(parts) > 1 else ""
    if lang == "zh" and country == "tw":
        return _LOCALE_RULES.get("tw", _LOCALE_RULES["en"])
    return _LOCALE_RULES.get(lang, _LOCALE_RULES["en"])


def _review_email_sequence(
    lead: dict[str, Any],
    *,
    locale: str,
    emails: list[dict[str, Any]],
    template_profile: dict[str, Any],
    template_plan: dict[str, Any],
    min_score: int,
    max_blocking_issues: int,
) -> dict[str, Any]:
    score = 100
    issues: list[str] = []
    suggestions: list[str] = []

    if len(emails) != 3:
        score -= 40
        issues.append("Expected exactly 3 emails in the sequence.")
        suggestions.append("Regenerate the full 3-step sequence before sending.")

    required_days = [0, 3, 7]
    previous_subject = ""
    for index, email in enumerate(emails[:3]):
        subject = str(email.get("subject", "") or "").strip()
        body = str(email.get("body_text", "") or "").strip()
        wc = len(body.split())
        if not subject:
            score -= 15
            issues.append(f"Email {index + 1} is missing a subject.")
        if wc < 50:
            score -= 20
            issues.append(f"Email {index + 1} body is too short ({wc} words).")
            suggestions.append(f"Expand Email {index + 1} to at least 50 words.")
        elif wc > 260:
            score -= 10
            issues.append(f"Email {index + 1} body is too long ({wc} words).")
            suggestions.append(f"Tighten Email {index + 1} for faster readability.")

        expected_day = required_days[index] if index < len(required_days) else None
        if expected_day is not None and email.get("suggested_send_day") != expected_day:
            score -= 5
            issues.append(f"Email {index + 1} send day should be {expected_day}.")

        lowered_subject = subject.lower()
        if previous_subject and lowered_subject == previous_subject:
            score -= 8
            issues.append(f"Email {index + 1} repeats the previous subject line.")
        previous_subject = lowered_subject

    if not str(template_plan.get("cta_strategy", "") or "").strip():
        score -= 8
        issues.append("Template plan is missing a CTA strategy.")
    if not str(template_profile.get("tone", "") or "").strip():
        score -= 5
        issues.append("Template profile is missing tone guidance.")

    company_name = str(lead.get("company_name", "") or "").strip()
    if company_name:
        personalization_hits = sum(
            1 for email in emails
            if company_name.lower() in str(email.get("body_text", "") or "").lower()
            or company_name.lower() in str(email.get("subject", "") or "").lower()
        )
        if personalization_hits == 0:
            score -= 10
            issues.append("Sequence does not mention the target company at all.")
            suggestions.append("Add at least one company-specific relevance reference.")

    status = "approved"
    if score < min_score or len(issues) > max_blocking_issues:
        status = "needs_review"

    return {
        "status": status,
        "score": max(score, 0),
        "issues": issues,
        "suggestions": suggestions,
        "min_score_required": min_score,
        "max_blocking_issues": max_blocking_issues,
        "blocking_issue_count": len(issues),
        "locale": locale,
    }


def _build_email_tools(llm: LLMTool, locale: str) -> list[ToolDef]:
    """Build the ReAct tool definitions for email validation."""
    rules = _get_locale_rules(locale)
    lang_name = rules["language"]
    formality = rules["formality"]
    salutation = rules["salutation"]
    closing = rules["closing"]
    rule_checks = "\n".join(f"  - {c}" for c in rules["checks"])

    async def tool_validate_emails(emails_json: str = "") -> str:
        """Validate a 3-email sequence for language correctness, formality, salutation format,
        and cultural appropriateness. Returns a validation report with issues and suggestions.
        Call this after drafting and after each revision.

        Args:
            emails_json: JSON string of the emails array (list of email objects).
        """
        if not emails_json or not emails_json.strip():
            return json.dumps({"passed": False, "issues": ["No emails provided"], "suggestions": []})

        from tools.llm_output import parse_json as _parse
        try:
            submitted = _parse(emails_json, context="validate_emails")
            if submitted is None:
                return json.dumps({"passed": False, "issues": ["Could not parse emails_json as JSON"], "suggestions": []})
            emails_list = submitted.get("emails", submitted) if isinstance(submitted, dict) else submitted
            if not isinstance(emails_list, list):
                emails_list = []
        except Exception as e:
            return json.dumps({"passed": False, "issues": [f"Parse error: {e}"], "suggestions": []})

        issues: list[str] = []
        suggestions: list[str] = []

        # Structural checks
        if len(emails_list) != 3:
            issues.append(f"Expected exactly 3 emails, got {len(emails_list)}")
            suggestions.append("Generate all 3 emails: company_intro, product_showcase, partnership_proposal")

        expected = [("company_intro", 0), ("product_showcase", 3), ("partnership_proposal", 7)]
        for i, (etype, eday) in enumerate(expected):
            if i < len(emails_list):
                em = emails_list[i]
                if em.get("email_type") != etype:
                    issues.append(f"Email {i+1}: email_type should be '{etype}', got '{em.get('email_type')}'")
                if em.get("suggested_send_day") != eday:
                    issues.append(f"Email {i+1}: suggested_send_day should be {eday}")
                if not em.get("subject", "").strip():
                    issues.append(f"Email {i+1}: subject is empty")
                body = em.get("body_text", "")
                wc = len(body.split())
                if wc < 50:
                    issues.append(f"Email {i+1}: body_text too short ({wc} words, min 50)")
                    suggestions.append(f"Email {i+1}: expand to 100-200 words")
                elif wc > 300:
                    issues.append(f"Email {i+1}: body_text too long ({wc} words, max 300)")

        # Language/cultural quality check via LLM
        sample = "\n---\n".join(
            f"Email {i+1} subject: {e.get('subject','')}\nBody: {e.get('body_text','')[:400]}"
            for i, e in enumerate(emails_list[:3])
        )
        validation_prompt = (
            f"You are a {lang_name} language expert and B2B communication specialist.\n"
            f"Locale: {locale} | Language: {lang_name} | Formality: {formality}\n"
            f"Expected salutation: {salutation}\n"
            f"Expected closing: {closing}\n\n"
            f"Validation rules:\n{rule_checks}\n\n"
            f"Emails to validate:\n{sample}\n\n"
            f"Check each email against ALL rules. Return JSON:\n"
            f'{{"passed": true/false, "language_correct": true/false, '
            f'"formality_correct": true/false, "salutation_correct": true/false, '
            f'"issues": ["..."], "suggestions": ["..."]}}\n'
            f"Be specific: mention which email number has which problem."
        )
        try:
            raw = await llm.generate(
                validation_prompt,
                system=f"You are a strict {lang_name} language and B2B communication validator. Return only JSON.",
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            from tools.llm_output import parse_json as _parse2
            llm_result = _parse2(raw, context="validate_emails_llm")
            if llm_result and isinstance(llm_result, dict):
                issues.extend(llm_result.get("issues", []))
                suggestions.extend(llm_result.get("suggestions", []))
                if not llm_result.get("language_correct", True):
                    issues.append(f"Language FAILED: emails are not fully in {lang_name}")
                if not llm_result.get("formality_correct", True):
                    issues.append(f"Formality FAILED: expected {formality} tone")
                if not llm_result.get("salutation_correct", True):
                    issues.append(f"Salutation FAILED: expected '{salutation}'")
        except Exception as e:
            logger.debug("[EmailCraft] LLM validation call failed: %s", e)

        return json.dumps({
            "passed": len(issues) == 0,
            "locale": locale,
            "language": lang_name,
            "issues": issues,
            "suggestions": suggestions,
            "expected_salutation": salutation,
            "expected_closing": closing,
        })

    return [
        ToolDef(
            name="validate_emails",
            description=(
                f"Validate the 3-email sequence for {lang_name} language correctness, "
                f"formality ({formality}), salutation format, cultural appropriateness, "
                f"and structural requirements (3 emails, correct types, 100-200 words each). "
                f"Returns pass/fail with specific issues and suggestions. "
                f"Call after drafting and after each revision."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "emails_json": {
                        "type": "string",
                        "description": "JSON string of the emails array to validate",
                    },
                },
                "required": ["emails_json"],
            },
            fn=tool_validate_emails,
        ),
    ]


async def _craft_for_lead(
    lead: dict,
    insight: dict,
    llm: LLMTool,
    semaphore: asyncio.Semaphore,
    *,
    email_template_examples: list[str] | None = None,
    email_template_notes: str = "",
    react_max_iterations: int = 3,
    hunt_id: str = "",
    hunt_round: int = 0,
) -> dict | None:
    """Generate a 3-email sequence for a single lead using a ReAct loop.

    Flow: Think → Draft → validate_emails → Revise (up to 2x) → Output JSON.

    Args:
        lead: Lead dict with company_name, website, industry, country_code, etc.
        insight: Company insight dict with company_name, products, etc.
        llm: LLMTool instance (shared, not closed here).
        semaphore: Concurrency limiter.
        react_max_iterations: Max ReAct iterations (default 3: draft + 2 revisions).
    """
    async with semaphore:
        settings = get_settings()
        locale = _get_locale(lead.get("country_code", ""))
        company_name = insight.get("company_name", "Our Company")
        products = ", ".join(insight.get("products", []))
        rules = _get_locale_rules(locale)
        template_profile = await extract_template_profile(
            llm,
            examples=list(email_template_examples or []),
            lead=lead,
            insight=insight,
            notes=email_template_notes,
        )
        template_plan = await compose_template_plan(
            llm,
            lead=lead,
            insight=insight,
            template_profile=template_profile,
            notes=email_template_notes,
        )

        user_prompt = (
            f"## Your Company\n"
            f"Name: {company_name}\n"
            f"Products: {products}\n\n"
            f"## Target Lead\n"
            f"Company: {lead.get('company_name', 'Unknown')}\n"
            f"Website: {lead.get('website', '')}\n"
            f"Industry: {lead.get('industry', 'Unknown')}\n"
            f"Description: {lead.get('description', '')}\n"
            f"Contact person: {lead.get('contact_person', 'Unknown')}\n"
            f"Known emails: {', '.join(lead.get('emails', [])) or 'none'}\n\n"
            f"## Locale\n"
            f"Locale: {locale}\n"
            f"Language: {rules['language']}\n"
            f"Formality: {rules['formality']}\n"
            f"Expected salutation: {rules['salutation']}\n"
            f"Expected closing: {rules['closing']}\n\n"
            f"## Template Guidance\n"
            f"Template source: {template_profile.get('source', 'auto_generated')}\n"
            f"Template notes: {email_template_notes}\n"
            f"Template profile: {json.dumps(template_profile, ensure_ascii=False)}\n"
            f"Template plan: {json.dumps(template_plan, ensure_ascii=False)}\n\n"
            f"Write the 3-email sequence in {rules['language']}. "
            f"Preserve the user's historical style when examples are present, "
            f"but adapt the content to this buyer and the template plan. "
            f"Call validate_emails after drafting, then revise if needed."
        )

        tools = _build_email_tools(llm, locale)

        try:
            raw = await react_loop(
                system=EMAIL_REACT_SYSTEM,
                user_prompt=user_prompt,
                tools=tools,
                settings=None,
                max_iterations=react_max_iterations,
                required_json_fields=["locale", "emails"],
                hunt_id=hunt_id,
                agent="email_craft",
                hunt_round=hunt_round,
            )
        except Exception as e:
            logger.warning("[EmailCraft] ReAct loop failed for %s: %s", lead.get("company_name"), e)
            return None

        from tools.llm_output import parse_json, validate_dict, EMAIL_SEQUENCE_REQUIRED, EMAIL_SEQUENCE_DEFAULTS
        parsed = parse_json(raw, context="EmailCraftAgent")
        if parsed is None:
            logger.warning("[EmailCraft] Unparseable output for %s", lead.get("company_name"))
            return None

        validated = validate_dict(parsed, EMAIL_SEQUENCE_REQUIRED, defaults=EMAIL_SEQUENCE_DEFAULTS, context="EmailCraftAgent")
        if validated is None or not validated.get("emails"):
            logger.warning("[EmailCraft] No emails in output for %s", lead.get("company_name"))
            return None

        emails = validated["emails"]
        review_summary = _review_email_sequence(
            lead,
            locale=locale,
            emails=emails,
            template_profile=template_profile,
            template_plan=template_plan,
            min_score=int(settings.email_review_min_score or 75),
            max_blocking_issues=int(settings.email_review_max_blocking_issues or 0),
        )
        logger.info("[EmailCraft] %s → %d emails in %s", lead.get("company_name"), len(emails), locale)

        return {
            "lead": lead,
            "locale": locale,
            "emails": emails,
            "template_profile": template_profile,
            "template_plan": template_plan,
            "review_summary": review_summary,
            "auto_send_eligible": review_summary["status"] == "approved",
        }


async def email_craft_node(state: HuntState) -> dict:
    """LangGraph node: concurrently generate email sequences for all leads.

    Each lead runs a ReAct loop (Think → Draft → Validate → Revise, max 3 iterations).
    Uses asyncio.Semaphore(email_gen_concurrency) to limit parallel LLM calls.

    Returns:
        Dict with 'email_sequences' list.
    """
    settings = get_settings()
    leads = state.get("leads", [])
    insight = state.get("insight")
    insight = insight if isinstance(insight, dict) else {}

    logger.info("[EmailCraftAgent] Starting — %d leads, ReAct max_iterations=%d",
                len(leads), settings.react_max_iterations)

    if not leads:
        logger.info("[EmailCraftAgent] No leads, skipping email generation")
        return {"email_sequences": [], "current_stage": "email_craft"}

    semaphore = asyncio.Semaphore(settings.email_gen_concurrency)
    hunt_id = state.get("hunt_id", "")
    hunt_round = state.get("hunt_round", 0)
    email_template_examples = list(state.get("email_template_examples", []) or [])
    email_template_notes = str(state.get("email_template_notes", "") or "")
    llm = LLMTool(
        hunt_id=hunt_id,
        agent="email_craft",
        hunt_round=hunt_round,
    )

    try:
        tasks = [
            _craft_for_lead(
                lead, insight, llm, semaphore,
                email_template_examples=email_template_examples,
                email_template_notes=email_template_notes,
                react_max_iterations=settings.react_max_iterations,
                hunt_id=hunt_id,
                hunt_round=hunt_round,
            )
            for lead in leads
        ]
        results = await asyncio.gather(*tasks)
    finally:
        await llm.close()

    email_sequences = [r for r in results if r is not None]

    logger.info("[EmailCraftAgent] Completed — %d/%d email sequences generated",
                len(email_sequences), len(leads))

    return {
        "email_sequences": email_sequences,
        "current_stage": "email_craft",
    }
