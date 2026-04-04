"""Queue-based producer/consumer runner for headless hunting."""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from automation.job_queue import HuntJobQueue
from config.settings import get_settings
from scripts.headless_worker import build_hunt_payload, run_hunt_payload


logger = logging.getLogger("hunt_queue")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _worker_id() -> str:
    return f"{socket.gethostname()}:{Path(__file__).name}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Persistent producer/consumer queue for AI Hunter")
    sub = parser.add_subparsers(dest="mode", required=True)

    producer = sub.add_parser("producer")
    producer.add_argument("--payload-file", default="")
    producer.add_argument("--website-url", default=None)
    producer.add_argument("--description", default=None)
    producer.add_argument("--product-keywords", nargs="*", default=[])
    producer.add_argument("--target-customer-profile", default=None)
    producer.add_argument("--target-regions", nargs="*", default=[])
    producer.add_argument("--target-lead-count", type=int, default=None)
    producer.add_argument("--max-rounds", type=int, default=None)
    producer.add_argument("--min-new-leads-threshold", type=int, default=None)
    producer.add_argument("--email-template-examples", nargs="*", default=[])
    producer.add_argument("--email-template-notes", default=None)
    producer.add_argument("--enable-email-craft", action=argparse.BooleanOptionalAction, default=None)
    producer.add_argument("--continuous", action=argparse.BooleanOptionalAction, default=False)
    producer.add_argument("--enqueue-interval-seconds", type=int, default=60)
    producer.add_argument("--max-pending-jobs", type=int, default=1)

    consumer = sub.add_parser("consumer")
    consumer.add_argument("--api-base-url", default="")
    consumer.add_argument("--api-token", default="")
    consumer.add_argument("--continuous", action=argparse.BooleanOptionalAction, default=False)
    consumer.add_argument("--poll-seconds", type=int, default=15)
    consumer.add_argument("--retry-delay-seconds", type=int, default=120)
    consumer.add_argument("--status-poll-seconds", type=int, default=15)
    consumer.add_argument("--request-timeout-seconds", type=int, default=60)
    consumer.add_argument("--auto-start-campaign", action=argparse.BooleanOptionalAction, default=True)
    consumer.add_argument("--campaign-name-prefix", default="Auto Campaign")

    return parser.parse_args(argv)


def run_producer(args: argparse.Namespace) -> int:
    settings = get_settings()
    queue = HuntJobQueue(settings.automation_queue_db_path)
    queue.init_db()
    payload = build_hunt_payload(args)

    while True:
        pending = queue.count_by_status("queued", "running")
        if pending < max(1, args.max_pending_jobs):
            job_id = queue.enqueue(payload, now_iso=_now_iso())
            logger.info("enqueued hunt job=%s pending=%s", job_id[:8], pending + 1)
        else:
            logger.info("producer skipped enqueue because pending=%s >= max_pending_jobs=%s", pending, args.max_pending_jobs)

        if not args.continuous:
            return 0
        time.sleep(max(1, args.enqueue_interval_seconds))


def run_consumer(args: argparse.Namespace) -> int:
    settings = get_settings()
    queue = HuntJobQueue(settings.automation_queue_db_path)
    queue.init_db()
    worker_id = _worker_id()

    consumer_args = argparse.Namespace(
        api_base_url=args.api_base_url or f"http://127.0.0.1:{settings.api_port}",
        api_token=args.api_token or settings.api_access_token,
        auto_start_campaign=args.auto_start_campaign,
        campaign_name_prefix=args.campaign_name_prefix,
        status_poll_seconds=args.status_poll_seconds,
        request_timeout_seconds=args.request_timeout_seconds,
    )

    while True:
        job = queue.claim_next(worker_id=worker_id, now_iso=_now_iso())
        if not job:
            if not args.continuous:
                return 0
            time.sleep(max(1, args.poll_seconds))
            continue

        logger.info("claimed job=%s", str(job['id'])[:8])
        try:
            result = run_hunt_payload(consumer_args, job.get("payload") or {})
            queue.mark_completed(str(job["id"]), hunt_id=str(result["hunt_id"]), finished_at=_now_iso())
            logger.info("completed job=%s hunt=%s", str(job["id"])[:8], str(result["hunt_id"])[:8])
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            available_at = (datetime.now(timezone.utc) + timedelta(seconds=max(1, args.retry_delay_seconds))).isoformat()
            queue.requeue(str(job["id"]), available_at=available_at, error_message=str(exc), updated_at=_now_iso())
            logger.exception("job=%s failed and was requeued: %s", str(job["id"])[:8], exc)
            if not args.continuous:
                return 1

        if not args.continuous:
            return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    if args.mode == "producer":
        return run_producer(args)
    if args.mode == "consumer":
        return run_consumer(args)
    raise SystemExit(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    raise SystemExit(main())
