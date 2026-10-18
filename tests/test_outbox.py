"""Outbox atomicity, retries, deduplication, and real transport request contracts."""
import logging
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import select, func, update

from app import outbox, email
from app.database import SessionLocal
from app.models import OutboxJob, Notification


def test_booking_outbox_and_console_email(client, organizer, customer, make_event, caplog):
    event = make_event(organizer, price=12345)
    with caplog.at_level(logging.INFO, logger="jtickets.email"):
        response = client.post("/bookings", headers=customer, json={"event_id": event["id"], "quantity": 2})
    assert response.status_code == 201
    with SessionLocal() as db:
        job = db.scalar(select(OutboxJob))
        assert job.kind == "booking_confirmation" and job.status == "done"
        assert job.payload == {"booking_id": response.json()["id"]}
        assert db.scalar(select(Notification.job_id)) == job.id
    assert "[EMAIL] console" in caplog.text
    assert "246.90" in caplog.text and "IST" in caplog.text
    assert response.json()["attendees"][0]["ticket_code"] in caplog.text


def test_task2_bulk_distinct_confirmed_bookers(client, organizer, customer, new_user, make_event, monkeypatch):
    event = make_event(organizer)
    other, cancelled_only, bystander = new_user("customer"), new_user("customer"), new_user("customer")
    for headers in (customer, customer, other):
        assert client.post("/bookings", headers=headers, json={"event_id": event["id"], "quantity": 1}).status_code == 201
    cancelled = client.post("/bookings", headers=cancelled_only, json={"event_id": event["id"], "quantity": 1}).json()
    assert client.delete(f"/bookings/{cancelled['id']}", headers=cancelled_only).status_code == 204
    # Inspect persisted work before dispatching it, then prove its recipient set.
    with monkeypatch.context() as patch:
        patch.setattr(outbox, "kick", lambda: None)
        r = client.put(f"/events/{event['id']}", headers=organizer, json={"venue": "New Patna Arena", "event_date": "2100-01-02T12:00:00+05:30"})
        assert r.status_code == 200
    with SessionLocal() as db:
        jobs = db.scalars(select(OutboxJob).where(OutboxJob.kind == "event_update")).all()
        assert len(jobs) == 2
        assert len({j.payload["user_id"] for j in jobs}) == 2
        assert all("event_date" in j.payload["summary"] and "New Patna Arena" in j.payload["summary"] and "IST" in j.payload["summary"] for j in jobs)
    assert outbox.drain(20) == 2
    for headers in (customer, other):
        notes = client.get("/notifications", headers=headers).json()
        assert len([n for n in notes if n["type"] == "event_updated"]) == 1
    for headers in (cancelled_only, bystander):
        assert not any(n["type"] == "event_updated" for n in client.get("/notifications", headers=headers).json())
    client.put(f"/events/{event['id']}", headers=organizer, json={"venue": "New Patna Arena"})
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(OutboxJob).where(OutboxJob.kind == "event_update")) == 2


def test_provider_failure_retries_without_duplicate_notification(client, organizer, customer, make_event, monkeypatch):
    event = make_event(organizer)
    sent = []
    def failing_send(*args):
        sent.append(args)
        raise email.EmailDeliveryError("Brevo email rejected (HTTP 503)")
    monkeypatch.setattr(email, "send_email", failing_send)
    r = client.post("/bookings", headers=customer, json={"event_id": event["id"], "quantity": 1})
    assert r.status_code == 201
    with SessionLocal() as db:
        job = db.scalar(select(OutboxJob))
        assert job.status == "pending" and job.attempts == 1
        assert job.next_attempt_at > datetime.now(timezone.utc).replace(tzinfo=None)
        assert "503" in job.last_error
        assert db.scalar(select(func.count()).select_from(Notification)) == 1
    assert outbox.drain() == 0  # backoff must be respected
    for attempt in range(2, 6):
        with SessionLocal() as db:
            db.execute(update(OutboxJob).values(next_attempt_at=datetime(2000, 1, 1)))
            db.commit()
        assert outbox.drain() == 1
        with SessionLocal() as db:
            job = db.scalar(select(OutboxJob))
            assert job.attempts == attempt
            assert job.status == ("failed" if attempt == 5 else "pending")
            assert db.scalar(select(func.count()).select_from(Notification)) == 1
    assert len(sent) == 5


def test_stuck_job_recovery_and_successful_retry(client, organizer, customer, make_event, monkeypatch):
    event = make_event(organizer)
    client.post("/bookings", headers=customer, json={"event_id": event["id"], "quantity": 1})
    with SessionLocal() as db:
        db.execute(update(OutboxJob).values(status="processing", updated_at=datetime(2000, 1, 1)))
        db.commit()
    sent = []
    monkeypatch.setattr(email, "send_email", lambda *args: sent.append(args))
    assert outbox.drain() == 1
    with SessionLocal() as db:
        assert db.scalar(select(OutboxJob.status)) == "done"
        assert db.scalar(select(func.count()).select_from(Notification)) == 1
    assert len(sent) == 1


def test_brevo_transport_and_suppression(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "brevo")
    monkeypatch.setenv("EMAIL_FROM", "sender@example.com")
    monkeypatch.setenv("BREVO_API_KEY", "unit-test-placeholder")
    requests = []
    def post(url, **kwargs):
        requests.append((url, kwargs))
        return httpx.Response(201)
    monkeypatch.setattr(email.httpx, "post", post)
    email.send_email("someone@example.com", "Subject", "<b>Body</b>", "Body")
    assert requests == []
    email.send_email("recipient@test.com", "Subject", "<b>Body</b>", "Body")
    url, kwargs = requests[0]
    assert url == "https://api.brevo.com/v3/smtp/email"
    assert kwargs["headers"] == {"api-key": "unit-test-placeholder"}
    assert kwargs["json"]["textContent"] == "Body" and kwargs["json"]["htmlContent"] == "<b>Body</b>"
    assert kwargs["timeout"] == 10
    monkeypatch.setattr(email.httpx, "post", lambda *a, **k: httpx.Response(429))
    with pytest.raises(RuntimeError, match="HTTP 429"):
        email.send_email("recipient@test.com", "Subject", "HTML", "Text")


def test_smtp_transport(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "smtp")
    monkeypatch.setenv("EMAIL_FROM", "sender@example.com")
    monkeypatch.setenv("SMTP_USER", "unit-test-user")
    monkeypatch.setenv("SMTP_PASSWORD", "unit-test-placeholder")
    calls = []
    class SMTP:
        def __init__(self, *a, **k): calls.append("connect")
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def starttls(self, **kwargs): calls.append("tls")
        def login(self, *a): calls.append("login")
        def send_message(self, message):
            calls.append("send")
            assert message.get_body(preferencelist=("plain",)).get_content().strip() == "Text"
            assert message.get_body(preferencelist=("html",)).get_content().strip() == "HTML"
            return {}
    monkeypatch.setattr(email.smtplib, "SMTP", SMTP)
    email.send_email("recipient@test.com", "Subject", "HTML", "Text")
    assert calls == ["connect", "tls", "login", "send"]


def test_html_escapes_user_content():
    html, text = email.template("<script>", ["<img src=x>"])
    assert "<script>" not in html and "&lt;img" in html
    assert "<img src=x>" in text


def test_multiple_dispatchers_claim_each_job_once(client, organizer, customer, make_event, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    event = make_event(organizer)
    with monkeypatch.context() as patch:
        patch.setattr(outbox, "kick", lambda: None)
        for _ in range(5):
            assert client.post("/bookings", headers=customer, json={"event_id": event["id"], "quantity": 1}).status_code == 201
    deliveries, lock = [], threading.Lock()
    def send(to, subject, html, text):
        with lock: deliveries.append(text)
    monkeypatch.setattr(email, "send_email", send)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: outbox.drain(), range(4)))
    # A claim lost to another worker may stop a drain pass; finish any pending
    # jobs just as the periodic dispatcher would.
    outbox.drain()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Notification)) == 5
        assert db.scalar(select(func.count()).select_from(OutboxJob).where(OutboxJob.status == "done")) == 5
    assert len(deliveries) == 5


def test_no_lifespan_kick_delivers_more_than_one_batch(client, organizer, customer, make_event, monkeypatch):
    event = make_event(organizer)
    with monkeypatch.context() as patch:
        patch.setattr(outbox, "kick", lambda: None)
        booking = client.post("/bookings", headers=customer, json={"event_id": event["id"], "quantity": 1}).json()
    with SessionLocal() as db:
        for _ in range(24):
            outbox.enqueue_booking_confirmation(db, booking["id"])
        db.commit()
    sent = []
    monkeypatch.setattr(email, "send_email", lambda *args: sent.append(args))
    outbox.kick()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(OutboxJob).where(OutboxJob.status == "done")) == 25
        assert db.scalar(select(func.count()).select_from(Notification)) == 25
    assert len(sent) == 25
