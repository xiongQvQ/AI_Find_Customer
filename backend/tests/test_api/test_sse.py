"""Tests for api/sse.py — SSE streaming, event format, hunt lifecycle events."""

import asyncio
import json

import pytest
from httpx import AsyncClient, ASGITransport

from api.app import create_app
from api.routes import _hunts, _sse_queues
from api.sse import _sse_event, _event_generator


@pytest.fixture
def app():
    _hunts.clear()
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestSseEventFormat:
    def test_event_format(self):
        result = _sse_event("stage_change", {"stage": "insight"})
        assert result.startswith("event: stage_change\n")
        assert "data: " in result
        assert result.endswith("\n\n")

        data_line = result.split("data: ")[1].strip()
        parsed = json.loads(data_line)
        assert parsed["stage"] == "insight"

    def test_event_unicode(self):
        result = _sse_event("progress", {"message": "Verarbeitung läuft"})
        assert "Verarbeitung läuft" in result


class TestEventGenerator:
    @pytest.mark.asyncio
    async def test_completed_hunt_emits_completed_event(self):
        _hunts["done-1"] = {
            "status": "completed",
            "result": {
                "leads": [{"company": "A"}, {"company": "B"}],
                "email_sequences": [{"locale": "en"}],
                "hunt_round": 3,
                "used_keywords": ["kw1", "kw2"],
            },
            "current_stage": "email_craft",
            "hunt_round": 3,
            "leads_count": 2,
            "email_sequences_count": 1,
            "error": None,
        }

        queue: asyncio.Queue = asyncio.Queue()
        events = []
        async for event in _event_generator("done-1", queue):
            events.append(event)

        # heartbeat + completed
        assert len(events) == 2
        assert "event: heartbeat" in events[0]
        assert "event: completed" in events[1]
        data = json.loads(events[1].split("data: ")[1].strip())
        assert data["leads_count"] == 2
        assert data["email_sequences_count"] == 1

    @pytest.mark.asyncio
    async def test_failed_hunt_emits_failed_event(self):
        _hunts["fail-1"] = {
            "status": "failed",
            "result": None,
            "current_stage": None,
            "hunt_round": 0,
            "leads_count": 0,
            "email_sequences_count": 0,
            "error": "API key invalid",
        }

        queue: asyncio.Queue = asyncio.Queue()
        events = []
        async for event in _event_generator("fail-1", queue):
            events.append(event)

        # heartbeat + failed
        assert len(events) == 2
        assert "event: heartbeat" in events[0]
        assert "event: failed" in events[1]
        data = json.loads(events[1].split("data: ")[1].strip())
        assert data["error"] == "API key invalid"

    @pytest.mark.asyncio
    async def test_queue_receives_broadcast_events(self):
        """Test that events pushed to the queue are yielded by the generator."""
        _hunts["running-1"] = {
            "status": "running",
            "result": None,
            "current_stage": "search",
            "hunt_round": 1,
            "leads_count": 5,
            "email_sequences_count": 0,
            "error": None,
        }

        queue: asyncio.Queue = asyncio.Queue()
        # Pre-load events into the queue
        queue.put_nowait(("stage_change", {"stage": "lead_extract", "hunt_round": 1, "leads_count": 5}))
        queue.put_nowait(("completed", {"leads_count": 10, "email_sequences_count": 0, "hunt_round": 2}))

        events = []
        async for event in _event_generator("running-1", queue):
            events.append(event)

        # heartbeat + stage_change + completed
        assert len(events) == 3
        assert "event: heartbeat" in events[0]
        assert "event: stage_change" in events[1]
        assert "event: completed" in events[2]


class TestSseEndpoint:
    @pytest.mark.asyncio
    async def test_stream_not_found(self, client):
        resp = await client.get("/api/v1/hunts/nonexistent/stream")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_stream_completed_hunt(self, client):
        _hunts["stream-1"] = {
            "status": "completed",
            "result": {
                "leads": [],
                "email_sequences": [],
                "hunt_round": 1,
                "used_keywords": [],
            },
            "current_stage": "email_craft",
            "hunt_round": 1,
            "leads_count": 0,
            "email_sequences_count": 0,
            "error": None,
        }

        resp = await client.get("/api/v1/hunts/stream-1/stream")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        body = resp.text
        assert "event: completed" in body
