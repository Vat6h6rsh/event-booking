"""Transactional producers and a recoverable, at-least-once job dispatcher."""
import logging
import os
import time
import threading
from datetime import timedelta

from sqlalchemy import select, update, insert, literal, func, cast, JSON

from app.database import SessionLocal
from app.email import EmailDeliveryError
from app.models import Booking, OutboxJob, utcnow

logger = logging.getLogger("jtickets.outbox")
_wake = threading.Event()
_stop = threading.Event()
_dispatcher = None
_lifecycle_lock = threading.Lock()


def enqueue_booking_confirmation(db, booking_id):
    db.add(OutboxJob(kind="booking_confirmation", payload={"booking_id": booking_id}))


def enqueue_event_update(db, event_id, summary):
    # One INSERT SELECT for the complete DISTINCT recipient set. PostgreSQL
    # JSON has no equality operator, so deduplicate user IDs before building JSON.
    recipients = select(Booking.user_id).where(
        Booking.event_id == event_id, Booking.status == "confirmed"
    ).distinct().subquery()
    json_object = func.json_object if db.bind.dialect.name == "sqlite" else func.json_build_object
    payload = json_object("user_id", recipients.c.user_id, "event_id", event_id, "summary", summary)
    # SQLite's json_object returns JSON text; CAST AS JSON applies numeric affinity.
    if db.bind.dialect.name != "sqlite": payload = cast(payload, JSON)
    now = utcnow()
    db.execute(insert(OutboxJob).from_select(
        ["kind", "payload", "status", "attempts", "next_attempt_at", "created_at", "updated_at"],
        select(literal("event_update"), payload, literal("pending"), literal(0),
               literal(now), literal(now), literal(now)).select_from(recipients),
    ))


def _recover():
    now = utcnow()
    with SessionLocal() as db:
        db.execute(update(OutboxJob).where(
            OutboxJob.status == "processing", OutboxJob.updated_at < now - timedelta(minutes=2)
        ).values(status="pending", next_attempt_at=now, updated_at=now))
        db.commit()


def _claim():
    now = utcnow()
    with SessionLocal() as db:
        ready = (OutboxJob.status == "pending", OutboxJob.next_attempt_at <= now)
        query = select(OutboxJob.id).where(*ready).order_by(OutboxJob.id).limit(1)
        if db.bind.dialect.name == "postgresql": query = query.with_for_update(skip_locked=True)
        job_id = db.scalar(query)
        if job_id is None: return None
        # Guarded UPDATE is essential on SQLite: two dispatchers may select the
        # same id. Claim one at a time so queued network calls cannot consume
        # another job's two-minute recovery lease.
        job = db.execute(update(OutboxJob).where(OutboxJob.id == job_id, *ready).values(
            status="processing", updated_at=now
        ).returning(OutboxJob)).scalar_one_or_none()
        if job is None: return None
        db.commit()
        return job


def _run(job):
    from app import tasks
    try:
        if job.kind == "booking_confirmation":
            tasks.send_booking_confirmation(job.payload["booking_id"], job.id)
        elif job.kind == "event_update":
            tasks.notify_event_update(job.payload["user_id"], job.payload["event_id"], job.payload["summary"], job.id)
        else:
            raise RuntimeError("Unknown outbox job kind")
    except Exception as exc:
        attempts = job.attempts + 1
        # Arbitrary exception text can expose credentials or user data. Only
        # transport errors from email.py have known, sanitized messages.
        error = type(exc).__name__
        if isinstance(exc, EmailDeliveryError):
            error += ": " + str(exc)[:200]
        values = dict(attempts=attempts, status="failed" if attempts >= 5 else "pending",
                      next_attempt_at=utcnow() + timedelta(seconds=10 * 2 ** (attempts - 1)),
                      last_error=error)
        logger.warning("Outbox job %s failed (%s), attempt %s", job.id, type(exc).__name__, attempts)
    else:
        values = dict(status="done", last_error=None)
    with SessionLocal() as db:
        db.execute(update(OutboxJob).where(
            OutboxJob.id == job.id, OutboxJob.status == "processing", OutboxJob.updated_at == job.updated_at
        ).values(**values, updated_at=utcnow()))
        db.commit()


def drain(max_jobs=20):
    _recover()
    count = 0
    while count < max_jobs:
        if threading.current_thread() is _dispatcher and _stop.is_set(): break
        job = _claim()
        if job is None: break
        _run(job)
        count += 1
    return count


def kick():
    if _dispatcher is not None and _dispatcher.is_alive():
        _wake.set()
    else:
        # Caller has already committed/released its connection. Without lifespan
        # (TestClient used directly), synchronous delivery is deterministic.
        try:
            while drain() == 20:
                pass
        except Exception:
            logger.exception("Outbox wake failed; persisted work will be retried by the dispatcher")


MAX_DEFER_SECONDS = float(os.getenv("OUTBOX_MAX_DEFER_SECONDS", "20"))


def _defer_while_busy():
    """Foreground first: while bookings are in flight, let them have the CPU/GIL.

    Jobs are already durable, so a short delay costs nothing but email latency; the
    cap guarantees background work is never starved by sustained traffic.
    """
    from app import middleware
    deadline = time.monotonic() + MAX_DEFER_SECONDS
    while middleware.inflight > 0 and time.monotonic() < deadline and not _stop.is_set():
        time.sleep(0.1)


def _loop():
    while not _stop.is_set():
        _wake.wait(5)
        _wake.clear()
        if _stop.is_set(): break
        _defer_while_busy()
        try:
            if drain() == 20: _wake.set()
        except Exception:
            logger.exception("Outbox dispatcher iteration failed")


def start():
    global _dispatcher
    with _lifecycle_lock:
        if _dispatcher is not None and _dispatcher.is_alive(): return
        _stop.clear()
        _wake.set()
        _dispatcher = threading.Thread(target=_loop, name="jtickets-outbox", daemon=True)
        _dispatcher.start()


def stop():
    global _dispatcher
    with _lifecycle_lock:
        if _dispatcher is None: return
        _stop.set()
        _wake.set()
        _dispatcher.join()
        _dispatcher = None
