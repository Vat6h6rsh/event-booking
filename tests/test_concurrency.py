"""
Concurrency safety — proves the `SELECT FOR UPDATE` row lock prevents overselling
the last ticket under simultaneous booking requests.

This is gated to PostgreSQL: `with_for_update()` is a genuine row-level lock there,
whereas on SQLite it is a no-op (SQLite has no row locks), so the guarantee cannot
be demonstrated on the default dev database. Run it with:

    docker compose up -d
    DATABASE_URL=postgresql://jtickets:jtickets_dev@localhost:5432/eventbooking pytest tests/test_concurrency.py
"""
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.database import engine

pytestmark = pytest.mark.skipif(
    engine.url.get_backend_name() == "sqlite",
    reason="row-level locking requires PostgreSQL (with_for_update is a no-op on SQLite)",
)


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
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 0
