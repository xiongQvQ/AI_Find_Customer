# Email Template Outreach

## Goal

Support two outbound email generation modes:

1. User provides historical outreach emails or template samples.
2. User provides no samples, so the system derives a reusable template plan from ICP and buyer insight.

## Request Fields

`HuntRequest` and `ResumeRequest` now support:

- `email_template_examples: list[str]`
- `email_template_notes: str`

## Generation Flow

The email pipeline now runs:

1. `extract_template_profile`
   Uses user-provided historical emails when available and extracts tone, subject style, opening style, CTA style, and guardrails.

2. `compose_template_plan`
   Combines seller ICP, buyer ICP, website/lead insight, and the extracted template profile into a reusable plan.

3. `email_craft_agent`
   Writes the actual 3-email sequence with:
   - locale rules
   - template profile
   - template plan
   - ReAct validation loop

## Design Choice

We do not ask the model to fully regenerate strategy from scratch inside the ReAct loop.
Instead:

- template extraction/composition happens before drafting
- ReAct is used only for drafting + validation + revision

This keeps style more stable and reduces prompt drift.
