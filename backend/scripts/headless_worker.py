"""Headless automation worker for continuous hunt -> campaign execution.

Run this script as a long-lived process on a VPS. It talks to the local API,
creates hunts, waits for completion, then optionally creates and starts an
email campaign for the generated sequences.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, request


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config.settings import get_settings
from automation.notifier import (
    render_hunt_completed_text,
    render_hunt_failed_text,
    render_hunt_started_text,
    send_feishu_text,
)


logger = logging.getLogger("headless_worker")


class ApiError(RuntimeError):
    """Raised when the local API returns a non-success response."""


class JobCancelledError(RuntimeError):
    """Raised when a queue job was cancelled while it was running."""


def _notify_feishu(text: str) -> None:
    settings = get_settings()
    webhook_url = str(settings.automation_feishu_webhook_url or "").strip()
    if not webhook_url:
        return
    send_feishu_text(webhook_url, text)


def _default_api_base_url() -> str:
    settings = get_settings()
    host = settings.api_host.strip() or "127.0.0.1"
    if host == "0.0.0.0":
        host = "127.0.0.1"
    return f"http://{host}:{settings.api_port}"


def _headers(api_token: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_token.strip():
        headers["X-API-Key"] = api_token.strip()
    return headers


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _request_json(
    *,
    method: str,
    base_url: str,
    path: str,
    api_token: str,
    payload: dict[str, Any] | None = None,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    url = f"{_normalize_base_url(base_url)}{path}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, method=method.upper(), headers=_headers(api_token))
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            return json.loads(raw)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ApiError(f"{method.upper()} {path} failed: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise ApiError(f"{method.upper()} {path} failed: {exc.reason}") from exc


def _prepare_template_seed(
    *,
    base_url: str,
    api_token: str,
    payload: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any] | None:
    if not bool(payload.get("enable_email_craft")):
        return None
    if isinstance(payload.get("template_seed"), dict):
        return payload.get("template_seed")
    request_payload = {
        "website_url": payload.get("website_url", ""),
        "description": payload.get("description", ""),
        "product_keywords": list(payload.get("product_keywords", []) or []),
        "target_customer_profile": payload.get("target_customer_profile", ""),
        "target_regions": list(payload.get("target_regions", []) or []),
        "uploaded_file_ids": list(payload.get("uploaded_file_ids", []) or payload.get("uploaded_files", []) or []),
        "email_template_examples": list(payload.get("email_template_examples", []) or []),
        "email_template_notes": payload.get("email_template_notes", ""),
    }
    response = _request_json(
        method="POST",
        base_url=base_url,
        path="/api/v1/email-template-seeds/prepare",
        api_token=api_token,
        payload=request_payload,
        timeout_seconds=timeout_seconds,
    )
    template_seed = response.get("template_seed")
    return template_seed if isinstance(template_seed, dict) else None


def _load_payload_file(path: str) -> dict[str, Any]:
    payload_path = Path(path).expanduser().resolve()
    data = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("payload file must contain a JSON object")
    return data


def build_hunt_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if args.payload_file:
        payload.update(_load_payload_file(args.payload_file))

    if args.website_url is not None:
        payload["website_url"] = args.website_url
    if args.description is not None:
        payload["description"] = args.description
    if args.product_keywords:
        payload["product_keywords"] = list(args.product_keywords)
    if args.target_customer_profile is not None:
        payload["target_customer_profile"] = args.target_customer_profile
    if args.target_regions:
        payload["target_regions"] = list(args.target_regions)
    if args.target_lead_count is not None:
        payload["target_lead_count"] = args.target_lead_count
    if args.max_rounds is not None:
        payload["max_rounds"] = args.max_rounds
    if args.min_new_leads_threshold is not None:
        payload["min_new_leads_threshold"] = args.min_new_leads_threshold
    if args.enable_email_craft is not None:
        payload["enable_email_craft"] = args.enable_email_craft
    if args.email_template_examples:
        payload["email_template_examples"] = list(args.email_template_examples)
    if args.email_template_notes is not None:
        payload["email_template_notes"] = args.email_template_notes

    payload.setdefault("website_url", "")
    payload.setdefault("description", "")
    payload.setdefault("product_keywords", [])
    payload.setdefault("target_customer_profile", "")
    payload.setdefault("target_regions", [])
    payload.setdefault("target_lead_count", 100)
    payload.setdefault("max_rounds", 10)
    payload.setdefault("min_new_leads_threshold", 5)
    payload.setdefault("enable_email_craft", True)
    payload.setdefault("email_template_examples", [])
    payload.setdefault("email_template_notes", "")

    if not payload["description"] and not payload["website_url"] and not payload["product_keywords"]:
        raise ValueError("description, website_url, or product_keywords is required")
    return payload


def _campaign_name(prefix: str, hunt_id: str) -> str:
    return f"{prefix} {hunt_id[:8]}".strip()


def _wait_for_hunt(
    *,
    base_url: str,
    api_token: str,
    hunt_id: str,
    poll_seconds: int,
    should_cancel: Any | None = None,
) -> dict[str, Any]:
    last_status = ""
    while True:
        if callable(should_cancel) and should_cancel():
            raise JobCancelledError(f"queue job cancelled while waiting for hunt {hunt_id}")
        status = _request_json(
            method="GET",
            base_url=base_url,
            path=f"/api/v1/hunts/{hunt_id}/status",
            api_token=api_token,
        )
        current = str(status.get("status", "") or "")
        stage = str(status.get("current_stage", "") or "")
        if current != last_status:
            logger.info(
                "hunt=%s status=%s stage=%s leads=%s emails=%s",
                hunt_id[:8],
                current,
                stage or "-",
                status.get("leads_count", 0),
                status.get("email_sequences_count", 0),
            )
            last_status = current
        if current in {"completed", "failed"}:
            return status
        time.sleep(max(1, poll_seconds))


def run_hunt_payload(args: argparse.Namespace, payload: dict[str, Any]) -> dict[str, Any]:
    progress_callback = getattr(args, "progress_callback", None)
    cancel_check = getattr(args, "cancel_check", None)

    def report(stage: str, message: str, **extra: Any) -> None:
        if callable(progress_callback):
            progress_callback(stage=stage, message=message, **extra)

    def ensure_not_cancelled() -> None:
        if callable(cancel_check) and cancel_check():
            raise JobCancelledError("Queue job cancelled by user")

    try:
        try:
            ensure_not_cancelled()
            report("template_seed", "Preparing email template seed", template_seed_status="preparing")
            template_seed = _prepare_template_seed(
                base_url=args.api_base_url,
                api_token=args.api_token,
                payload=payload,
                timeout_seconds=args.request_timeout_seconds,
            )
            if template_seed is not None:
                payload = dict(payload)
                payload["template_seed"] = template_seed
                report(
                    "template_seed",
                    "Template seed prepared",
                    template_seed_status="ready",
                    template_seed_source=str(template_seed.get("source", "") or "pre_generated"),
                )
                logger.info("prepared template seed before hunt creation")
        except Exception as exc:
            report("template_seed", f"Template seed preparation failed: {exc}", template_seed_status="failed")
            logger.warning("template seed preparation failed, continuing without pre-generated seed: %s", exc)

        ensure_not_cancelled()
        report("create_hunt", "Creating hunt from queue job")
        created = _request_json(
            method="POST",
            base_url=args.api_base_url,
            path="/api/v1/hunts",
            api_token=args.api_token,
            payload=payload,
            timeout_seconds=args.request_timeout_seconds,
        )
        hunt_id = str(created["hunt_id"])
        report("hunt_created", "Hunt created, waiting for execution", hunt_id=hunt_id)
        logger.info(
            "created hunt=%s target_leads=%s email_craft=%s",
            hunt_id[:8],
            payload.get("target_lead_count"),
            payload.get("enable_email_craft"),
        )
        try:
            _notify_feishu(render_hunt_started_text(payload, hunt_id=hunt_id))
        except Exception as exc:
            logger.warning("failed to send start notification for hunt=%s: %s", hunt_id[:8], exc)
    except Exception as exc:
        try:
            _notify_feishu(render_hunt_failed_text(payload, error_message=str(exc)))
        except Exception as notify_exc:
            logger.warning("failed to send failure notification before hunt start: %s", notify_exc)
        raise

    try:
        ensure_not_cancelled()
        report("wait_hunt", "Consumer is polling hunt status", hunt_id=hunt_id)
        status = _wait_for_hunt(
            base_url=args.api_base_url,
            api_token=args.api_token,
            hunt_id=hunt_id,
            poll_seconds=args.status_poll_seconds,
            should_cancel=cancel_check,
        )
        if str(status.get("status", "")) != "completed":
            raise ApiError(f"hunt {hunt_id} failed: {status.get('error', 'unknown error')}")

        ensure_not_cancelled()
        report("load_result", "Loading completed hunt result", hunt_id=hunt_id)
        result = _request_json(
            method="GET",
            base_url=args.api_base_url,
            path=f"/api/v1/hunts/{hunt_id}/result",
            api_token=args.api_token,
            timeout_seconds=args.request_timeout_seconds,
        )
        leads = result.get("leads") or []
        sequences = result.get("email_sequences") or []
        logger.info(
            "completed hunt=%s leads=%s email_sequences=%s",
            hunt_id[:8],
            len(leads) if isinstance(leads, list) else 0,
            len(sequences) if isinstance(sequences, list) else 0,
        )

        campaign_summary: dict[str, Any] | None = None
        if args.auto_start_campaign and payload.get("enable_email_craft"):
            ensure_not_cancelled()
            report("create_campaign", "Creating campaign from approved email sequences", hunt_id=hunt_id)
            created_campaign = _request_json(
                method="POST",
                base_url=args.api_base_url,
                path=f"/api/v1/hunts/{hunt_id}/email-campaigns",
                api_token=args.api_token,
                payload={"name": _campaign_name(args.campaign_name_prefix, hunt_id)},
                timeout_seconds=args.request_timeout_seconds,
            )
            campaign_id = str(created_campaign["campaign_id"])
            sequence_count = int(created_campaign.get("sequence_count", 0) or 0)
            logger.info("campaign=%s created sequence_count=%s", campaign_id[:8], sequence_count)
            if sequence_count > 0:
                ensure_not_cancelled()
                report("start_campaign", "Starting campaign and handing off to scheduler", hunt_id=hunt_id)
                campaign_summary = _request_json(
                    method="POST",
                    base_url=args.api_base_url,
                    path=f"/api/v1/email-campaigns/{campaign_id}/start",
                    api_token=args.api_token,
                    timeout_seconds=args.request_timeout_seconds,
                )
                logger.info("campaign=%s started", campaign_id[:8])
            else:
                report("campaign_draft", "Campaign created but no send-ready sequences were available", hunt_id=hunt_id)
                campaign_summary = {"campaign_id": campaign_id, "status": "draft", "sequence_count": 0}
                logger.warning("campaign=%s has no send-ready sequences", campaign_id[:8])

        final_result = {
            "hunt_id": hunt_id,
            "website_url": str(payload.get("website_url", "") or ""),
            "lead_count": len(leads) if isinstance(leads, list) else 0,
            "email_sequence_count": len(sequences) if isinstance(sequences, list) else 0,
            "campaign": campaign_summary,
        }
        report("completed", "Queue job completed", hunt_id=hunt_id)
        _notify_feishu(render_hunt_completed_text(final_result))
        return final_result
    except Exception as exc:
        report("failed", f"Queue job failed: {exc}", hunt_id=hunt_id)
        try:
            _notify_feishu(render_hunt_failed_text(payload, error_message=str(exc)))
        except Exception as notify_exc:
            logger.warning("failed to send failure notification for hunt=%s: %s", hunt_id[:8], notify_exc)
        raise


def run_cycle(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_hunt_payload(args)
    return run_hunt_payload(args, payload)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run AI Hunter continuously without the web UI.",
    )
    parser.add_argument("--api-base-url", default=_default_api_base_url())
    parser.add_argument("--api-token", default=get_settings().api_access_token)
    parser.add_argument("--payload-file", default="")
    parser.add_argument("--website-url", default=None)
    parser.add_argument("--description", default=None)
    parser.add_argument("--product-keywords", nargs="*", default=[])
    parser.add_argument("--target-customer-profile", default=None)
    parser.add_argument("--target-regions", nargs="*", default=[])
    parser.add_argument("--target-lead-count", type=int, default=None)
    parser.add_argument("--max-rounds", type=int, default=None)
    parser.add_argument("--min-new-leads-threshold", type=int, default=None)
    parser.add_argument("--email-template-examples", nargs="*", default=[])
    parser.add_argument("--email-template-notes", default=None)
    parser.add_argument(
        "--enable-email-craft",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Generate AI email sequences after hunting. Defaults to true if omitted.",
    )
    parser.add_argument(
        "--auto-start-campaign",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Create and start a campaign automatically after a successful hunt.",
    )
    parser.add_argument("--campaign-name-prefix", default="Auto Campaign")
    parser.add_argument(
        "--continuous",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run forever instead of a single cycle.",
    )
    parser.add_argument("--cycle-interval-seconds", type=int, default=60)
    parser.add_argument("--status-poll-seconds", type=int, default=15)
    parser.add_argument("--request-timeout-seconds", type=int, default=60)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    while True:
        try:
            result = run_cycle(args)
            logger.info("cycle finished: %s", json.dumps(result, ensure_ascii=False))
        except KeyboardInterrupt:
            logger.info("stopped by user")
            return 0
        except Exception as exc:
            logger.exception("cycle failed: %s", exc)
            if not args.continuous:
                return 1
        if not args.continuous:
            return 0
        time.sleep(max(1, args.cycle_interval_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
