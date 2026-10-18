"""Inventory, idempotency and API hardening from LLD sections 3-8."""
import hashlib
import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select, func

from app import schemas
from app.database import SessionLocal
from app.models import Booking, IdempotencyKey, OutboxJob, Notification, utcnow


def _book(client, customer, event, quantity=1, **body):
    return client.post("/bookings", headers=customer,
                       json={"event_id": event["id"], "quantity": quantity, **body})


def _tier(client, organizer, event, total=6):
    r = client.post(f"/events/{event['id']}/tiers", headers=organizer,
                    json={"name": "VIP", "price": 12345, "total_seats": total})
    assert r.status_code == 201, r.text
    return r.json()


def test_idempotent_replay_and_mismatch(client, organizer, customer, make_event):
    event = make_event(organizer)
    headers = {**customer, "Idempotency-Key": "one-booking-intent"}
    body = {"event_id": event["id"], "quantity": 2}
    first = client.post("/bookings", headers=headers, json=body)
    replay = client.post("/bookings", headers=headers, json=body)
    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.headers["Idempotent-Replayed"] == "true"
    assert replay.json() == first.json()
    mismatch = client.post("/bookings", headers=headers, json={**body, "quantity": 3})
    assert mismatch.status_code == 422
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Booking)) == 1
        assert db.scalar(select(func.count()).select_from(OutboxJob)) == 1
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 8


def test_inflight_and_expired_idempotency_key(client, organizer, customer, make_event):
    event = make_event(organizer)
    body = schemas.BookingCreate(event_id=event["id"], quantity=1)
    fingerprint = hashlib.sha256(json.dumps(body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    user = client.get("/users/me", headers=customer).json()
    with SessionLocal() as db:
        db.add(IdempotencyKey(user_id=user["id"], key="in-flight", request_hash=fingerprint))
        db.commit()
    headers = {**customer, "Idempotency-Key": "in-flight"}
    assert client.post("/bookings", headers=headers, json=body.model_dump()).status_code == 409
    with SessionLocal() as db:
        key = db.scalar(select(IdempotencyKey))
        key.created_at = utcnow() - timedelta(hours=25)
        db.commit()
    assert client.post("/bookings", headers=headers, json=body.model_dump()).status_code == 201


def test_failed_booking_rolls_back_key_inventory_and_outbox(client, organizer, customer, make_event):
    event = make_event(organizer)
    headers = {**customer, "Idempotency-Key": "retry-after-validation"}
    r = client.post("/bookings", headers=headers, json={"event_id": event["id"], "quantity": 1, "tier_id": 999999})
    assert r.status_code == 404
    with SessionLocal() as db:
        for model in (IdempotencyKey, Booking, OutboxJob, Notification):
            assert db.scalar(select(func.count()).select_from(model)) == 0
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 10
    assert client.post("/bookings", headers=headers, json={"event_id": event["id"], "quantity": 1}).status_code == 201


def test_tier_and_base_share_event_capacity(client, organizer, customer, make_event):
    event = make_event(organizer)
    tier = _tier(client, organizer, event)
    booking = _book(client, customer, event, 6, tier_id=tier["id"])
    assert booking.status_code == 201
    assert booking.json()["total_price"] == 6 * 12345
    current = client.get(f"/events/{event['id']}").json()
    assert current["available_tickets"] == 4
    assert current["tiers"][0]["available_seats"] == 0
    # An unavailable tier rolls the event decrement back too.
    assert _book(client, customer, event, 1, tier_id=tier["id"]).status_code == 409
    assert _book(client, customer, event, 4).status_code == 201
    assert _book(client, customer, event).status_code == 409
    assert client.delete(f"/bookings/{booking.json()['id']}", headers=customer).status_code == 204
    assert client.delete(f"/bookings/{booking.json()['id']}", headers=customer).status_code == 409
    current = client.get(f"/events/{event['id']}").json()
    assert current["available_tickets"] == 6
    assert current["tiers"][0]["available_seats"] == 6


def test_capacity_and_tier_update_guards(client, organizer, customer, make_event):
    event = make_event(organizer)
    tier = _tier(client, organizer, event)
    path = f"/events/{event['id']}"
    assert client.post(path + "/tiers", headers=organizer, json={"name": "Extra", "price": 0, "total_seats": 5}).status_code == 422
    assert client.put(path + f"/tiers/{tier['id']}", headers=organizer, json={"total_seats": 11}).status_code == 422
    assert _book(client, customer, event, 4, tier_id=tier["id"]).status_code == 201
    assert client.put(path + f"/tiers/{tier['id']}", headers=organizer, json={"total_seats": 3}).status_code == 422
    assert client.put(path, headers=organizer, json={"total_tickets": 5}).status_code == 422
    r = client.put(path, headers=organizer, json={"total_tickets": 12})
    assert r.status_code == 200
    assert r.json()["available_tickets"] == 8
    r = client.put(path + f"/tiers/{tier['id']}", headers=organizer, json={"total_seats": 8})
    assert r.status_code == 200
    assert r.json()["available_seats"] == 4
    # Base sales count when reducing event capacity too.
    assert _book(client, customer, event, 6).status_code == 201
    assert client.put(path, headers=organizer, json={"total_tickets": 9}).status_code == 422


@pytest.mark.parametrize("quantity", [0, -1, 11, 99])
def test_quantity_bounds(client, organizer, customer, make_event, quantity):
    event = make_event(organizer)
    assert _book(client, customer, event, quantity).status_code == 422


@pytest.mark.parametrize("attendees", [[{"full_name": "Only one"}], [{"full_name": "One"}, {"full_name": "Two"}, {"full_name": "Three"}]])
def test_attendee_length_must_match(client, organizer, customer, make_event, attendees):
    event = make_event(organizer)
    assert _book(client, customer, event, 2, attendees=attendees).status_code == 422


@pytest.mark.parametrize("attendees", [None, [], [{"full_name": "Missing age"}], [{"full_name": "Minor", "age": 17}]])
def test_restricted_event_requires_all_ages(client, organizer, customer, make_event, attendees):
    event = make_event(organizer, age_rating="18+")
    assert _book(client, customer, event, attendees=attendees).status_code == 400
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 10


def test_cancel_after_start_rejected(client, organizer, customer, make_event):
    event = make_event(organizer, event_date="2000-01-01T12:00:00")
    booking = _book(client, customer, event).json()
    assert client.delete(f"/bookings/{booking['id']}", headers=customer).status_code == 409
    assert client.get(f"/bookings/{booking['id']}", headers=customer).json()["status"] == "confirmed"


@pytest.mark.parametrize("values", [{"price": -1}, {"total_tickets": 0}, {"name": ""}, {"name": None}, {"event_date": None}, {"price": None}, {"status": "completed"}, {"age_rating": "anything"}])
def test_invalid_event_updates(client, organizer, make_event, values):
    event = make_event(organizer)
    assert client.put(f"/events/{event['id']}", headers=organizer, json=values).status_code == 422


def test_dates_validated_against_existing_values(client, organizer, make_event):
    event = make_event(organizer, end_date="2099-12-02T20:00:00")
    path = f"/events/{event['id']}"
    assert client.put(path, headers=organizer, json={"event_date": "2100-01-01T12:00:00"}).status_code == 422
    assert client.put(path, headers=organizer, json={"end_date": "2099-11-01T12:00:00"}).status_code == 422
    assert client.put(path, headers=organizer, json={"end_date": None}).status_code == 200


def test_event_list_filters_and_health(client, organizer, make_event):
    venue = client.post("/venues", headers=organizer, json={
        "name": "Hall", "address": "Road", "city": "Ranchi", "capacity": 20,
    }).json()
    event = make_event(organizer, name="Jazz Evening", venue_id=venue["id"])
    make_event(organizer, name="Other", venue="Patna Arena")
    assert [e["id"] for e in client.get("/events", params={"city": "ranch", "q": "jazz"}).json()] == [event["id"]]
    assert len(client.get("/events", params={"city": "patna"}).json()) == 1
    assert client.get("/events?limit=101").status_code == 422
    health = client.get("/").json()
    assert health["db"] == "ok" and health["outbox_pending"] == 0


def test_booking_response_does_not_query_after_commit(client, organizer, customer, make_event, monkeypatch):
    import threading
    from sqlalchemy import event as sql_event
    from sqlalchemy.orm import Session
    from app import outbox
    from app.database import engine
    event = make_event(organizer)
    phase = threading.local()
    original_commit = Session.commit
    def commit(db):
        original_commit(db)
        phase.committed = True
    def before_query(*args):
        assert not getattr(phase, "committed", False), "Booking response opened a post-commit transaction"
    monkeypatch.setattr(Session, "commit", commit)
    monkeypatch.setattr(outbox, "kick", lambda: None)
    sql_event.listen(engine, "before_cursor_execute", before_query)
    try:
        response = _book(client, customer, event, 2)
        assert response.status_code == 201
        assert len(response.json()["attendees"]) == 2
        assert response.json()["event_name"] == event["name"]
    finally:
        sql_event.remove(engine, "before_cursor_execute", before_query)
