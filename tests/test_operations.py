"""Admission control, lifespan, key configuration and database safety."""
import asyncio
import threading

import httpx
import pytest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import auth, outbox
from app.database import SessionLocal
from app.main import app
from app.middleware import BookingAdmissionMiddleware
from app.models import OutboxJob
from conftest import validate_test_database


def test_admission_timeout_has_cors_and_releases_slot():
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        async def downstream(scope, receive, send):
            entered.set()
            await release.wait()
            await send({"type": "http.response.start", "status": 201, "headers": []})
            await send({"type": "http.response.body", "body": b"{}"})
        wrapped = CORSMiddleware(BookingAdmissionMiddleware(downstream, max_inflight=1, queue_timeout=.05), allow_origins=["http://localhost:5173"])
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=wrapped), base_url="http://test") as client:
            first = asyncio.create_task(client.post("/bookings"))
            await entered.wait()
            rejected = await client.post("/bookings", headers={"Origin": "http://localhost:5173"})
            assert rejected.status_code == 503
            assert rejected.json() == {"detail": "High demand - please retry in a moment"}
            assert rejected.headers["Retry-After"] == "2"
            assert rejected.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
            release.set()
            assert (await first).status_code == 201
            assert (await client.post("/bookings")).status_code == 201
    asyncio.run(scenario())


def test_admission_disconnect_releases_slot():
    async def scenario():
        entered = asyncio.Event()
        async def downstream(scope, receive, send):
            entered.set()
            await asyncio.Event().wait()
        wrapped = BookingAdmissionMiddleware(downstream, max_inflight=1, queue_timeout=.05)
        async def receive(): return {"type": "http.request", "body": b""}
        async def send(message): pass
        scope = {"type": "http", "method": "POST", "path": "/bookings"}
        running = asyncio.create_task(wrapped(scope, receive, send))
        await entered.wait()
        running.cancel()
        with pytest.raises(asyncio.CancelledError): await running
        assert wrapped._semaphores[asyncio.get_running_loop()].locked() is False
    asyncio.run(scenario())


def test_lifespan_dispatches_pending_job(client, organizer, customer, make_event, monkeypatch):
    event = make_event(organizer)
    with monkeypatch.context() as patch:
        patch.setattr(outbox, "kick", lambda: None)
        assert client.post("/bookings", headers=customer, json={"event_id": event["id"], "quantity": 1}).status_code == 201
    sent = threading.Event()
    from app import email
    monkeypatch.setattr(email, "send_email", lambda *args: sent.set())
    with TestClient(app):
        assert sent.wait(10)
    assert outbox._dispatcher is None
    with SessionLocal() as db:
        assert db.scalar(select(OutboxJob.status)) == "done"


def test_postgres_requires_long_secret(monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_URL", "postgresql://localhost/jtickets_test")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="at least 32"): auth.validate_secret()
    monkeypatch.setenv("SECRET_KEY", "short")
    with pytest.raises(RuntimeError, match="at least 32"): auth.validate_secret()
    monkeypatch.setenv("SECRET_KEY", "x" * 32)
    assert len(auth.validate_secret()) == 32


@pytest.mark.parametrize("url", ["postgresql://localhost/eventbooking", "sqlite:///booking.db", "postgresql://test-user@localhost/production"])
def test_test_database_guard_rejects_unsafe_targets(url):
    with pytest.raises(RuntimeError, match="Refusing non-test"): validate_test_database(url)


def test_health_reports_database_failure(client, monkeypatch):
    import app.main as main
    def fail(): raise OSError("database unavailable")
    monkeypatch.setattr(main, "SessionLocal", fail)
    response = client.get("/")
    assert response.status_code == 503
    assert response.json()["db"] == "error"


def test_organizer_event_stats_are_scoped_and_aggregate_confirmed(client, organizer, customer, make_event):
    ev = make_event(organizer, total_tickets=50, price=1000)
    for qty in (2, 3):
        r = client.post("/bookings", json={"event_id": ev["id"], "quantity": qty}, headers=customer)
        assert r.status_code == 201, r.text
    client.delete(f"/bookings/{r.json()['id']}", headers=customer)
    stats = client.get("/events/mine/stats", headers=organizer)
    assert stats.status_code == 200
    row = next(s for s in stats.json() if s["event_id"] == ev["id"])
    assert row == {"event_id": ev["id"], "confirmed_bookings": 1, "tickets_sold": 2,
                   "gross_paise": 2000, "cancelled_bookings": 1}
    assert client.get("/events/mine/stats", headers=customer).status_code == 403
