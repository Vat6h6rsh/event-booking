"""Conditional inventory writes must prevent overselling on SQLite and PostgreSQL."""
from concurrent.futures import ThreadPoolExecutor


def test_last_ticket_is_not_oversold(client, organizer, customer, make_event):
    event = make_event(organizer, total_tickets=1)

    def book(_):
        return client.post(
            "/bookings", json={"event_id": event["id"], "quantity": 1}, headers=customer
        ).status_code

    with ThreadPoolExecutor(max_workers=10) as pool:
        statuses = list(pool.map(book, range(10)))

    # Exactly one request wins the single ticket; the rest are told it's sold out.
    assert statuses.count(201) == 1, statuses
    assert statuses.count(409) == 9, statuses
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 0


def test_small_event_concurrent_bookings_never_oversell(client, organizer, customer, make_event):
    event = make_event(organizer, total_tickets=5)
    def book(_):
        return client.post("/bookings", headers=customer, json={"event_id": event["id"], "quantity": 1}).status_code
    with ThreadPoolExecutor(max_workers=25) as pool:
        statuses = list(pool.map(book, range(25)))
    assert statuses.count(201) == 5, statuses
    assert statuses.count(409) == 20, statuses
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 0
    bookings = client.get("/bookings", headers=customer).json()
    assert sum(b["quantity"] for b in bookings) == 5


def test_concurrent_idempotent_requests_create_one_booking(client, organizer, customer, make_event):
    event = make_event(organizer)
    def book(_):
        return client.post("/bookings", headers={**customer, "Idempotency-Key": "same-concurrent-intent"},
                           json={"event_id": event["id"], "quantity": 1})
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(book, range(10)))
    assert [r.status_code for r in results].count(201) == 1
    assert all(r.status_code in (200, 201) for r in results), [r.text for r in results]
    assert len({r.json()["id"] for r in results}) == 1
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 9


def test_concurrent_duplicate_cancel_restores_once(client, organizer, customer, make_event):
    event = make_event(organizer)
    tier = client.post(f"/events/{event['id']}/tiers", headers=organizer,
                       json={"name": "VIP", "price": 0, "total_seats": 10}).json()
    booking = client.post("/bookings", headers=customer, json={"event_id": event["id"], "quantity": 3, "tier_id": tier["id"]}).json()
    def cancel(_):
        return client.delete(f"/bookings/{booking['id']}", headers=customer).status_code
    with ThreadPoolExecutor(max_workers=10) as pool:
        statuses = list(pool.map(cancel, range(10)))
    assert statuses.count(204) == 1, statuses
    assert statuses.count(409) == 9, statuses
    event = client.get(f"/events/{event['id']}").json()
    assert event["available_tickets"] == 10 and event["tiers"][0]["available_seats"] == 10


def test_concurrent_tier_adds_cannot_overallocate(client, organizer, make_event):
    event = make_event(organizer, total_tickets=5)
    def add(_):
        return client.post(f"/events/{event['id']}/tiers", headers=organizer,
                           json={"name": "Tier", "price": 0, "total_seats": 3}).status_code
    with ThreadPoolExecutor(max_workers=5) as pool:
        statuses = list(pool.map(add, range(5)))
    assert statuses.count(201) == 1, statuses
    assert statuses.count(422) == 4, statuses
