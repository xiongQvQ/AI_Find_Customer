"""EmailCraftAgent — concurrent 3-email sequence generation per lead, multi-language.

Uses a ReAct loop (Think → Draft → Validate → Revise) with max 3 iterations.
The validate_emails tool checks language correctness, formality, salutation format,
and cultural norms per locale before the agent finalises the output.
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import logging
import re
from typing import Any

from config.settings import get_settings
from emailing.policy import choose_email_target
from emailing.template_pipeline import compose_template_plan, extract_template_profile
from graph.state import HuntState
from tools.llm_client import LLMTool
from tools.llm_output import parse_json
from tools.react_runner import ToolDef, react_loop

logger = logging.getLogger(__name__)

_DEFAULT_TEMPLATE_MAX_SEND_COUNT = 100

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


EMAIL_FEWSHOT_EXAMPLES = """
## Example A — English, distributor outreach
{
  "locale": "en_US",
  "emails": [
    {
      "sequence_number": 1,
      "email_type": "company_intro",
      "subject": "Potential fit for your industrial components range",
      "body_text": "Dear Mr. Carter, I noticed your company supplies industrial electrical components to OEM and maintenance customers. We manufacture switch components used in appliance and control-system applications, and your product mix suggests there could be relevance. If this category is of interest, I can send a short overview of the most relevant models and certifications. Best regards,",
      "suggested_send_day": 0,
      "personalization_points": ["industrial components range"],
      "cultural_adaptations": ["professional English", "low-friction CTA"]
    }
  ]
}

## Example B — German, formal buyer outreach
{
  "locale": "de_DE",
  "emails": [
    {
      "sequence_number": 1,
      "email_type": "company_intro",
      "subject": "Mögliche Relevanz für Ihr Sortiment im Bereich Schaltkomponenten",
      "body_text": "Sehr geehrte Damen und Herren, Ihrem Unternehmensprofil nach beliefern Sie industrielle Kunden mit elektrischen Komponenten. Wir fertigen Schalter und verwandte Baugruppen für Haushaltsgeräte und Steuerungssysteme. Daher könnte es Berührungspunkte mit Ihrem Sortiment geben. Wenn das Thema für Sie relevant ist, sende ich Ihnen gern eine kurze Übersicht der passenden Modelle und Zertifizierungen. Mit freundlichen Grüßen,",
      "suggested_send_day": 0,
      "personalization_points": ["industrielle Kunden", "elektrische Komponenten"],
      "cultural_adaptations": ["formal German salutation", "direct but polite CTA"]
    }
  ]
}

## Example C — Simplified Chinese, business style
{
  "locale": "zh_CN",
  "emails": [
    {
      "sequence_number": 1,
      "email_type": "company_intro",
      "subject": "或许与贵司现有产品线相关的开关器件",
      "body_text": "您好，从贵司公开资料来看，贵司在工业电气/配套器件领域具备较强的分销与供货能力。我们主要生产微动开关及相关组件，适用于家电和控制系统场景，因此与贵司现有业务可能存在一定匹配度。如您方便，我可以先发一版精简的产品与认证信息，供贵司初步评估。期待您的回复。",
      "suggested_send_day": 0,
      "personalization_points": ["工业电气", "分销与供货能力"],
      "cultural_adaptations": ["formal business Chinese", "polite low-pressure CTA"]
    }
  ]
}
"""


LANGUAGE_SELECTOR_SYSTEM = """You are a B2B email language-routing specialist.

Choose the best language for an outbound business email.

Priority:
1. Maximise the chance the recipient can read and respond comfortably.
2. Prefer the language clearly evidenced by the lead's public-facing communication.
3. If evidence is weak or mixed, prefer English.
4. Do not force a local language only because of country if business evidence suggests English is safer.

Return JSON only:
{
  "chosen_language": "...",
  "chosen_locale": "...",
  "confidence": "high|medium|low",
  "reason": "...",
  "fallback_used": true
}"""


BRIEF_SYNTHESIS_SYSTEM = """You are a B2B outbound strategist.

Do not write the emails yet.
Prepare a concise strategy brief for a 3-step outbound sequence.

The brief must be grounded in actual facts from:
- the seller's products, positioning, and ICP
- the buyer's industry, website, profile, and lead evidence

Do not invent facts.
Do not use vague generic value propositions unless directly supported.
Prefer concrete buyer relevance over generic sales language.

Return JSON only."""


EMAIL_REWRITER_SYSTEM = """You are an expert international B2B email editor.

You will receive:
- the target locale and language requirements
- the current 3-email sequence JSON
- a list of validation issues and rewrite instructions

Your task is to revise the sequence so it:
- fixes every issue
- preserves factual accuracy
- remains natural for the local business culture
- keeps the 3-email progression distinct

Return JSON only in the same schema as the original sequence."""


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


def _locale_for_language(language_code: str, fallback_locale: str = "en_US") -> str:
    normalized = str(language_code or "").strip().lower()
    if not normalized:
        return fallback_locale
    mapping = {
        "en": "en_US",
        "de": "de_DE",
        "fr": "fr_FR",
        "es": "es_ES",
        "pt": "pt_PT",
        "it": "it_IT",
        "nl": "nl_NL",
        "pl": "pl_PL",
        "ru": "ru_RU",
        "ja": "ja_JP",
        "ko": "ko_KR",
        "zh": "zh_CN",
        "zh-cn": "zh_CN",
        "zh-tw": "zh_TW",
        "ar": "ar_SA",
        "tr": "tr_TR",
    }
    return mapping.get(normalized, fallback_locale)


def _slugify_template_segment(value: str, fallback: str = "general") -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return normalized or fallback


def _derive_template_group(
    lead: dict[str, Any],
    *,
    target: dict[str, str],
    locale: str,
) -> str:
    target_type = _slugify_template_segment(target.get("target_type", ""), "contact")
    industry = _slugify_template_segment(lead.get("industry", ""), "general")
    return f"{locale}|{target_type}|{industry}"


def _template_id_for_group(group_key: str) -> str:
    digest = hashlib.sha1(group_key.encode("utf-8")).hexdigest()[:12]
    return f"tpl_{digest}"


def _replace_template_tokens(
    value: str,
    *,
    source_lead: dict[str, Any],
    target_lead: dict[str, Any],
    source_target: dict[str, str],
    target_target: dict[str, str],
) -> str:
    updated = str(value or "")
    replacements = [
        (str(source_lead.get("company_name", "") or ""), str(target_lead.get("company_name", "") or "")),
        (str(source_lead.get("industry", "") or ""), str(target_lead.get("industry", "") or "")),
        (str(source_target.get("target_name", "") or ""), str(target_target.get("target_name", "") or "")),
        (str(source_target.get("target_title", "") or ""), str(target_target.get("target_title", "") or "")),
        (str(source_target.get("target_email", "") or ""), str(target_target.get("target_email", "") or "")),
    ]
    for source_value, target_value in replacements:
        if source_value and target_value and source_value in updated:
            updated = updated.replace(source_value, target_value)
    return updated


def _apply_template_to_lead(
    template_result: dict[str, Any],
    *,
    lead: dict[str, Any],
    target: dict[str, str],
    template_group: str,
    template_index: int,
    template_assigned_count: int,
    template_max_send_count: int,
) -> dict[str, Any]:
    cloned = copy.deepcopy(template_result)
    source_lead = cloned.get("lead", {})
    source_target = cloned.get("target", {})
    template_id = _template_id_for_group(template_group)
    adapted_emails: list[dict[str, Any]] = []

    for email in cloned.get("emails", []):
        updated_email = copy.deepcopy(email)
        updated_email["subject"] = _replace_template_tokens(
            updated_email.get("subject", ""),
            source_lead=source_lead,
            target_lead=lead,
            source_target=source_target,
            target_target=target,
        )
        updated_email["body_text"] = _replace_template_tokens(
            updated_email.get("body_text", ""),
            source_lead=source_lead,
            target_lead=lead,
            source_target=source_target,
            target_target=target,
        )
        points = list(updated_email.get("personalization_points", []))
        lead_company = str(lead.get("company_name", "") or "").strip()
        lead_industry = str(lead.get("industry", "") or "").strip()
        target_title = str(target.get("target_title", "") or "").strip()
        if lead_company and lead_company not in points:
            points.append(lead_company)
        if lead_industry and lead_industry not in points:
            points.append(lead_industry)
        if target_title and target_title not in points:
            points.append(target_title)
        updated_email["personalization_points"] = points
        adapted_emails.append(updated_email)

    cloned["lead"] = lead
    cloned["target"] = target
    cloned["emails"] = adapted_emails
    cloned["template_group"] = template_group
    cloned["template_id"] = template_id
    cloned["template_usage_index"] = template_index
    cloned["generation_mode"] = "template_pool"
    cloned["template_reused"] = template_index > 1
    cloned["template_max_send_count"] = template_max_send_count
    cloned["template_assigned_count"] = template_assigned_count
    cloned["template_remaining_capacity"] = max(template_max_send_count - template_assigned_count, 0)
    cloned["template_performance"] = {
        "sent_count": 0,
        "replied_count": 0,
        "reply_rate": 0.0,
        "status": "warming_up",
    }
    return cloned


def _rule_validate_emails_payload(emails_list: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[str] = []
    suggestions: list[str] = []

    if len(emails_list) != 3:
        issues.append(f"Expected exactly 3 emails, got {len(emails_list)}")
        suggestions.append("Generate all 3 emails: company_intro, product_showcase, partnership_proposal")

    expected = [("company_intro", 0), ("product_showcase", 3), ("partnership_proposal", 7)]
    previous_subject = ""
    for i, (etype, eday) in enumerate(expected):
        if i >= len(emails_list):
            break
        em = emails_list[i]
        if em.get("email_type") != etype:
            issues.append(f"Email {i + 1}: email_type should be '{etype}', got '{em.get('email_type')}'")
        if em.get("suggested_send_day") != eday:
            issues.append(f"Email {i + 1}: suggested_send_day should be {eday}")
        if not str(em.get("subject", "") or "").strip():
            issues.append(f"Email {i + 1}: subject is empty")
        body = str(em.get("body_text", "") or "")
        wc = len(body.split())
        if wc < 50:
            issues.append(f"Email {i + 1}: body_text too short ({wc} words, min 50)")
            suggestions.append(f"Email {i + 1}: expand to 100-200 words")
        elif wc > 300:
            issues.append(f"Email {i + 1}: body_text too long ({wc} words, max 300)")

        lowered_body = body.lower()
        lowered_subject = str(em.get("subject", "") or "").lower()
        if not any(token in lowered_body for token in ["you", "your", "您", "贵公司", "votre", "ihr", "su ", "sua ", "vos", "tu empresa"]):
            issues.append(f"Email {i + 1}: lacks clear buyer-oriented language")
            suggestions.append(f"Email {i + 1}: explain why this recipient/company is relevant")
        if any(phrase in lowered_body for phrase in ["leading provider", "world-class", "best-in-class", "industry-leading"]) and wc < 120:
            issues.append(f"Email {i + 1}: relies on generic marketing claims")
            suggestions.append(f"Email {i + 1}: replace generic superlatives with concrete proof points")
        if previous_subject and previous_subject == lowered_subject:
            issues.append(f"Email {i + 1}: subject repeats previous email")
        previous_subject = lowered_subject

    if len(emails_list) == 3:
        email_1 = str(emails_list[0].get("body_text", "") or "").lower()
        email_2 = str(emails_list[1].get("body_text", "") or "").lower()
        email_3 = str(emails_list[2].get("body_text", "") or "").lower()
        if email_1[:120] == email_2[:120]:
            issues.append("Email 2 repeats Email 1 instead of deepening relevance")
            suggestions.append("Use Email 2 to add product/application fit or proof points")
        if any(token in email_3 for token in ["urgent", "last chance", "final notice"]):
            issues.append("Email 3 CTA is too aggressive for cold outreach")
            suggestions.append("Use a lighter follow-up or qualification CTA in Email 3")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
    }


async def _locale_validate_emails_payload(
    llm: LLMTool,
    locale: str,
    emails_list: list[dict[str, Any]],
) -> dict[str, Any]:
    rules = _get_locale_rules(locale)
    lang_name = rules["language"]
    formality = rules["formality"]
    salutation = rules["salutation"]
    closing = rules["closing"]
    rule_checks = "\n".join(f"  - {c}" for c in rules["checks"])
    sample = "\n---\n".join(
        f"Email {i+1} subject: {e.get('subject','')}\nBody: {e.get('body_text','')[:700]}"
        for i, e in enumerate(emails_list[:3])
    )
    validation_prompt = (
        f"You are a {lang_name} language expert and B2B communication specialist.\n"
        f"Locale: {locale} | Language: {lang_name} | Formality: {formality}\n"
        f"Expected salutation: {salutation}\n"
        f"Expected closing: {closing}\n\n"
        f"Validation rules:\n{rule_checks}\n\n"
        f"Emails to validate:\n{sample}\n\n"
        f"Check each email against ALL rules. Also verify: grammar, spelling, punctuation, local business naturalness, tone, buyer relevance, concrete seller value, low-friction CTA, and whether the 3 emails progress instead of repeating.\n"
        f"Return JSON:\n"
        f'{{"passed": true/false, "grammar_ok": true/false, "spelling_ok": true/false, "language_correct": true/false, '
        f'"formality_correct": true/false, "salutation_correct": true/false, "business_etiquette_ok": true/false, '
        f'"local_naturalness_ok": true/false, "commercial_quality": true/false, "sequence_progression": true/false, '
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
        if not isinstance(raw, str):
            raise TypeError("locale validator returned non-string output")
        parsed = parse_json(raw, context="locale_validate_emails")
        if isinstance(parsed, dict):
            return parsed
    except Exception as exc:
        logger.debug("[EmailCraft] Locale validator failed for %s: %s", locale, exc)
    return {
        "passed": True,
        "grammar_ok": True,
        "spelling_ok": True,
        "language_correct": True,
        "formality_correct": True,
        "salutation_correct": True,
        "business_etiquette_ok": True,
        "local_naturalness_ok": True,
        "commercial_quality": True,
        "sequence_progression": True,
        "issues": [],
        "suggestions": [],
    }


async def _rewrite_email_sequence(
    llm: LLMTool,
    *,
    locale: str,
    rules: dict[str, Any],
    user_prompt: str,
    current_sequence: dict[str, Any],
    issues: list[str],
    suggestions: list[str],
) -> dict[str, Any] | None:
    rewrite_prompt = (
        f"<locale>\n"
        f"locale: {locale}\n"
        f"language: {rules['language']}\n"
        f"formality: {rules['formality']}\n"
        f"salutation: {rules['salutation']}\n"
        f"closing: {rules['closing']}\n"
        f"</locale>\n\n"
        f"<context>\n{user_prompt}\n</context>\n\n"
        f"<current_sequence>\n{json.dumps(current_sequence, ensure_ascii=False)}\n</current_sequence>\n\n"
        f"<issues>\n{json.dumps(issues, ensure_ascii=False)}\n</issues>\n\n"
        f"<rewrite_instructions>\n{json.dumps(suggestions, ensure_ascii=False)}\n</rewrite_instructions>"
    )
    try:
        raw = await llm.generate(
            rewrite_prompt,
            system=EMAIL_REWRITER_SYSTEM,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        if not isinstance(raw, str):
            return None
        parsed = parse_json(raw, context="email_rewriter")
        if isinstance(parsed, dict):
            return parsed
    except Exception as exc:
        logger.debug("[EmailCraft] Rewriter failed for locale %s: %s", locale, exc)
    return None


async def _validate_and_revise_sequence(
    llm: LLMTool,
    *,
    locale: str,
    rules: dict[str, Any],
    user_prompt: str,
    parsed_sequence: dict[str, Any],
    max_revisions: int = 2,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    current = parsed_sequence
    last_summary = {
        "passed": False,
        "status": "needs_review",
        "issues": ["Validation did not run"],
        "suggestions": [],
    }
    for _ in range(max_revisions + 1):
        emails_list = current.get("emails", []) if isinstance(current, dict) else []
        if not isinstance(emails_list, list) or not emails_list:
            return None, last_summary

        rule_result = _rule_validate_emails_payload(emails_list)
        locale_result = await _locale_validate_emails_payload(llm, locale, emails_list)

        issues = list(rule_result.get("issues", []))
        suggestions = list(rule_result.get("suggestions", []))
        issues.extend(locale_result.get("issues", []))
        suggestions.extend(locale_result.get("suggestions", []))

        if not locale_result.get("grammar_ok", True):
            issues.append("Grammar FAILED: emails contain grammar issues")
        if not locale_result.get("spelling_ok", True):
            issues.append("Spelling FAILED: emails contain spelling issues")
        if not locale_result.get("language_correct", True):
            issues.append(f"Language FAILED: emails are not fully in {rules['language']}")
        if not locale_result.get("formality_correct", True):
            issues.append(f"Formality FAILED: expected {rules['formality']} tone")
        if not locale_result.get("salutation_correct", True):
            issues.append(f"Salutation FAILED: expected '{rules['salutation']}'")
        if not locale_result.get("business_etiquette_ok", True):
            issues.append("Business etiquette FAILED: wording does not fit local business email habits")
        if not locale_result.get("local_naturalness_ok", True):
            issues.append("Local naturalness FAILED: wording feels translated or culturally unnatural")
        if not locale_result.get("commercial_quality", True):
            issues.append("Commercial quality FAILED: sequence is too generic or not buyer-relevant enough")
        if not locale_result.get("sequence_progression", True):
            issues.append("Sequence progression FAILED: emails do not clearly build on each other")

        dedup_issues = list(dict.fromkeys(str(item) for item in issues if str(item).strip()))
        dedup_suggestions = list(dict.fromkeys(str(item) for item in suggestions if str(item).strip()))

        last_summary = {
            "passed": len(dedup_issues) == 0,
            "status": "approved" if len(dedup_issues) == 0 else "needs_review",
            "issues": dedup_issues,
            "suggestions": dedup_suggestions,
        }

        if not dedup_issues:
            return current, last_summary

        revised = await _rewrite_email_sequence(
            llm,
            locale=locale,
            rules=rules,
            user_prompt=user_prompt,
            current_sequence=current,
            issues=dedup_issues,
            suggestions=dedup_suggestions,
        )
        if revised is None:
            return current, last_summary
        current = revised

    return current, last_summary


def _fallback_language_choice(
    lead: dict[str, Any],
    *,
    default_locale: str,
    language_mode: str,
    default_language: str,
    fallback_language: str,
) -> dict[str, Any]:
    website = str(lead.get("website", "") or "")
    description = str(lead.get("description", "") or "")
    target_title = str(lead.get("target_title", "") or "")
    evidence_text = f"{website} {description} {target_title}".lower()
    if language_mode == "manual":
        chosen = default_language or fallback_language or "en"
        return {
            "chosen_language": chosen,
            "chosen_locale": _locale_for_language(chosen, default_locale),
            "confidence": "high",
            "reason": "manual language mode",
            "fallback_used": chosen != default_locale.split("_")[0].lower(),
        }
    if language_mode == "english_only":
        return {
            "chosen_language": "en",
            "chosen_locale": "en_US",
            "confidence": "high",
            "reason": "english_only mode",
            "fallback_used": True,
        }
    if any(token in evidence_text for token in ["/en", "english", "global", "international"]):
        return {
            "chosen_language": "en",
            "chosen_locale": "en_US",
            "confidence": "medium",
            "reason": "public-facing evidence suggests English is safer",
            "fallback_used": True,
        }
    return {
        "chosen_language": default_locale.split("_")[0].lower(),
        "chosen_locale": default_locale,
        "confidence": "medium",
        "reason": "country/locale default",
        "fallback_used": False,
    }


async def _select_email_language(
    lead: dict[str, Any],
    target: dict[str, str],
    llm: LLMTool,
    *,
    default_locale: str,
    language_mode: str,
    default_language: str,
    fallback_language: str,
) -> dict[str, Any]:
    fallback_choice = _fallback_language_choice(
        lead,
        default_locale=default_locale,
        language_mode=language_mode,
        default_language=default_language,
        fallback_language=fallback_language,
    )
    prompt = (
        f"<settings>\n"
        f"language_mode: {language_mode}\n"
        f"default_language: {default_language}\n"
        f"fallback_language: {fallback_language}\n"
        f"</settings>\n\n"
        f"<lead>\n"
        f"company_name: {lead.get('company_name', '')}\n"
        f"website: {lead.get('website', '')}\n"
        f"description: {lead.get('description', '')}\n"
        f"country_code: {lead.get('country_code', '')}\n"
        f"contact_name: {target.get('target_name', '')}\n"
        f"contact_title: {target.get('target_title', '')}\n"
        f"</lead>\n\n"
        f"<instructions>\n"
        f"Choose the most appropriate outbound email language.\n"
        f"Use local language only when there is strong evidence it is the better business choice.\n"
        f"If uncertain, choose English.\n"
        f"</instructions>"
    )
    try:
        raw = await llm.generate(
            prompt,
            system=LANGUAGE_SELECTOR_SYSTEM,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        if not isinstance(raw, str):
            return fallback_choice
        parsed = parse_json(raw, context="email_language_selector")
        if isinstance(parsed, dict) and parsed.get("chosen_language"):
            chosen_locale = parsed.get("chosen_locale") or _locale_for_language(
                str(parsed.get("chosen_language", "")),
                default_locale,
            )
            return {
                "chosen_language": str(parsed.get("chosen_language", fallback_choice["chosen_language"])),
                "chosen_locale": str(chosen_locale),
                "confidence": str(parsed.get("confidence", fallback_choice["confidence"])),
                "reason": str(parsed.get("reason", fallback_choice["reason"])),
                "fallback_used": bool(parsed.get("fallback_used", fallback_choice["fallback_used"])),
            }
    except Exception as exc:
        logger.debug("[EmailCraft] Language selector failed for %s: %s", lead.get("company_name"), exc)
    return fallback_choice


async def _synthesise_email_brief(
    lead: dict[str, Any],
    insight: dict[str, Any],
    target: dict[str, str],
    llm: LLMTool,
) -> dict[str, Any]:
    fallback_brief = {
        "recipient_profile": str(lead.get("industry", "") or "Potential distributor or buyer"),
        "why_this_company_may_fit": [
            str(lead.get("industry", "") or "Operates in a relevant industry"),
            str(lead.get("description", "") or "Public profile suggests potential buyer relevance"),
        ],
        "best_value_angles": list((insight.get("value_propositions") or [])[:2]) or [
            "Relevant product portfolio for distributor conversations",
            "Potential long-term supply partnership",
        ],
        "product_focus": list((insight.get("products") or [])[:2]),
        "proof_points_to_use": list((insight.get("value_propositions") or [])[:2]),
        "claims_to_avoid": ["Avoid unverifiable superlatives", "Avoid generic mass-email phrasing"],
        "cta_strategy": "Ask a low-friction qualification question about category ownership or interest.",
        "tone_guidance": "Professional, concise, commercially credible.",
        "personalization_hooks": [
            str(lead.get("company_name", "") or ""),
            str(lead.get("description", "") or ""),
            str(target.get("target_title", "") or ""),
        ],
    }
    prompt = (
        f"<seller_company>\n"
        f"name: {insight.get('company_name', '')}\n"
        f"summary: {insight.get('summary', '')}\n"
        f"products: {json.dumps(insight.get('products', []), ensure_ascii=False)}\n"
        f"industries: {json.dumps(insight.get('industries', []), ensure_ascii=False)}\n"
        f"value_propositions: {json.dumps(insight.get('value_propositions', []), ensure_ascii=False)}\n"
        f"target_customer_profile: {insight.get('target_customer_profile', '')}\n"
        f"negative_targeting_criteria: {json.dumps(insight.get('negative_targeting_criteria', []), ensure_ascii=False)}\n"
        f"</seller_company>\n\n"
        f"<buyer_company>\n"
        f"company_name: {lead.get('company_name', '')}\n"
        f"website: {lead.get('website', '')}\n"
        f"industry: {lead.get('industry', '')}\n"
        f"description: {lead.get('description', '')}\n"
        f"country_code: {lead.get('country_code', '')}\n"
        f"contact_name: {target.get('target_name', '')}\n"
        f"contact_title: {target.get('target_title', '')}\n"
        f"target_email_type: {target.get('target_type', '')}\n"
        f"fit_score: {lead.get('fit_score', lead.get('match_score', ''))}\n"
        f"contactability_score: {lead.get('contactability_score', '')}\n"
        f"</buyer_company>\n\n"
        f"<task>\n"
        f"Build an outbound strategy brief.\n"
        f"Focus on why this buyer may care, which products are most relevant, what proof points are credible, and what CTA is appropriate for a first cold outreach.\n"
        f"</task>"
    )
    try:
        raw = await llm.generate(
            prompt,
            system=BRIEF_SYNTHESIS_SYSTEM,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        if not isinstance(raw, str):
            return fallback_brief
        parsed = parse_json(raw, context="email_brief_synthesizer")
        if isinstance(parsed, dict):
            merged = fallback_brief | parsed
            return merged
    except Exception as exc:
        logger.debug("[EmailCraft] Brief synthesis failed for %s: %s", lead.get("company_name"), exc)
    return fallback_brief
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
        rule_result = _rule_validate_emails_payload(emails_list)
        issues = list(rule_result["issues"])
        suggestions = list(rule_result["suggestions"])

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
            f'"commercial_quality": true/false, "sequence_progression": true/false, '
            f'"issues": ["..."], "suggestions": ["..."]}}\n'
            f"Also verify: buyer relevance, concrete seller value, low-friction CTA, and that the 3 emails progress instead of repeating.\n"
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
                if not llm_result.get("commercial_quality", True):
                    issues.append("Commercial quality FAILED: sequence is too generic or not buyer-relevant enough")
                if not llm_result.get("sequence_progression", True):
                    issues.append("Sequence progression FAILED: emails do not clearly build on each other")
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
        target = choose_email_target(lead)
        if not target.get("target_email"):
            logger.info("[EmailCraft] Skipping %s — no sendable email target", lead.get("company_name"))
            return None
        settings = get_settings()
        default_locale = _get_locale(lead.get("country_code", ""))
        language_choice = await _select_email_language(
            lead,
            target,
            llm,
            default_locale=default_locale,
            language_mode=settings.email_language_mode,
            default_language=settings.email_default_language,
            fallback_language=settings.email_fallback_language,
        )
        locale = str(language_choice.get("chosen_locale", default_locale) or default_locale)
        company_name = insight.get("company_name", "Our Company")
        products = ", ".join(insight.get("products", []))
        rules = _get_locale_rules(locale)
        strategy_brief = await _synthesise_email_brief(lead, insight, target, llm)
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
            f"Summary: {insight.get('summary', '')}\n"
            f"Industries: {', '.join(insight.get('industries', []))}\n"
            f"Value propositions: {'; '.join(insight.get('value_propositions', []))}\n"
            f"Ideal customer profile: {insight.get('target_customer_profile', '')}\n\n"
            f"## Target Lead\n"
            f"Company: {lead.get('company_name', 'Unknown')}\n"
            f"Website: {lead.get('website', '')}\n"
            f"Industry: {lead.get('industry', 'Unknown')}\n"
            f"Description: {lead.get('description', '')}\n"
            f"Contact person: {lead.get('contact_person', 'Unknown')}\n"
            f"Known emails: {', '.join(lead.get('emails', [])) or 'none'}\n"
            f"Target email: {target.get('target_email', '')}\n"
            f"Target contact name: {target.get('target_name', '')}\n"
            f"Target contact title: {target.get('target_title', '')}\n"
            f"Target type: {target.get('target_type', '')}\n\n"
            f"Fit score: {lead.get('fit_score', lead.get('match_score', ''))}\n"
            f"Contactability score: {lead.get('contactability_score', '')}\n\n"
            f"## Locale\n"
            f"Locale: {locale}\n"
            f"Language: {rules['language']}\n"
            f"Formality: {rules['formality']}\n"
            f"Expected salutation: {rules['salutation']}\n"
            f"Expected closing: {rules['closing']}\n"
            f"Language selection reason: {language_choice.get('reason', '')}\n"
            f"Fallback used: {language_choice.get('fallback_used', False)}\n\n"
            f"## Strategy Brief\n"
            f"Recipient profile: {strategy_brief.get('recipient_profile', '')}\n"
            f"Why this company may fit: {json.dumps(strategy_brief.get('why_this_company_may_fit', []), ensure_ascii=False)}\n"
            f"Best value angles: {json.dumps(strategy_brief.get('best_value_angles', []), ensure_ascii=False)}\n"
            f"Product focus: {json.dumps(strategy_brief.get('product_focus', []), ensure_ascii=False)}\n"
            f"Proof points to use: {json.dumps(strategy_brief.get('proof_points_to_use', []), ensure_ascii=False)}\n"
            f"Claims to avoid: {json.dumps(strategy_brief.get('claims_to_avoid', []), ensure_ascii=False)}\n"
            f"CTA strategy: {strategy_brief.get('cta_strategy', '')}\n"
            f"Tone guidance: {strategy_brief.get('tone_guidance', '')}\n"
            f"Personalization hooks: {json.dumps(strategy_brief.get('personalization_hooks', []), ensure_ascii=False)}\n\n"
            f"## Sequence Objectives\n"
            f"Email 1: establish relevance and open the conversation with a low-friction CTA.\n"
            f"Email 2: deepen relevance using product/application fit or proof points.\n"
            f"Email 3: polite follow-up that probes distributor/buyer fit without pressure.\n\n"
            f"## Style Examples\n"
            f"{EMAIL_FEWSHOT_EXAMPLES}\n\n"
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

        from tools.llm_output import validate_dict, EMAIL_SEQUENCE_REQUIRED, EMAIL_SEQUENCE_DEFAULTS
        parsed = parse_json(raw, context="EmailCraftAgent")
        if parsed is None:
            logger.warning("[EmailCraft] Unparseable output for %s", lead.get("company_name"))
            return None

        revised, validation_summary = await _validate_and_revise_sequence(
            llm,
            locale=locale,
            rules=rules,
            user_prompt=user_prompt,
            parsed_sequence=parsed,
            max_revisions=2,
        )
        if revised is None:
            logger.warning("[EmailCraft] Validation/revision produced no usable emails for %s", lead.get("company_name"))
            return None

        validated = validate_dict(revised, EMAIL_SEQUENCE_REQUIRED, defaults=EMAIL_SEQUENCE_DEFAULTS, context="EmailCraftAgent")
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
            "target": target,
            "language_choice": language_choice,
            "strategy_brief": strategy_brief,
            "validation_summary": validation_summary,
            "review_status": validation_summary.get("status", "approved"),
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

    grouped_leads: dict[str, list[tuple[dict[str, Any], dict[str, str]]]] = {}
    for lead in leads:
        target = choose_email_target(lead)
        if not target.get("target_email"):
            logger.info("[EmailCraftAgent] Skipping %s — no sendable email target", lead.get("company_name"))
            continue
        template_group = _derive_template_group(
            lead,
            target=target,
            locale=_get_locale(lead.get("country_code", "")),
        )
        grouped_leads.setdefault(template_group, []).append((lead, target))

    async def _generate_group_seed(group_key: str, seed_lead: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
        result = await _craft_for_lead(
            seed_lead,
            insight,
            llm,
            semaphore,
            email_template_examples=email_template_examples,
            email_template_notes=email_template_notes,
            react_max_iterations=settings.react_max_iterations,
            hunt_id=hunt_id,
            hunt_round=hunt_round,
        )
        return group_key, result

    try:
        seed_tasks = [
            _generate_group_seed(group_key, members[0][0])
            for group_key, members in grouped_leads.items()
        ]
        seed_results = await asyncio.gather(*seed_tasks)
    finally:
        await llm.close()

    template_results = {group_key: result for group_key, result in seed_results if result is not None}
    email_sequences: list[dict[str, Any]] = []
    template_max_send_count = int(getattr(settings, "email_template_max_send_count", _DEFAULT_TEMPLATE_MAX_SEND_COUNT) or _DEFAULT_TEMPLATE_MAX_SEND_COUNT)
    for group_key, members in grouped_leads.items():
        template_result = template_results.get(group_key)
        if template_result is None:
            continue
        template_assigned_count = len(members)
        for index, (lead, target) in enumerate(members, start=1):
            email_sequences.append(
                _apply_template_to_lead(
                    template_result,
                    lead=lead,
                    target=target,
                    template_group=group_key,
                    template_index=index,
                    template_assigned_count=template_assigned_count,
                    template_max_send_count=template_max_send_count,
                )
            )

    logger.info("[EmailCraftAgent] Completed — %d/%d email sequences generated",
                len(email_sequences), len(leads))

    return {
        "email_sequences": email_sequences,
        "current_stage": "email_craft",
    }
