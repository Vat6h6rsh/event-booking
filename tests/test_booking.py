"""Booking flow: inventory accounting, over-booking guard, cancellation, age gate."""


def test_booking_decrements_inventory(client, organizer, customer, make_event):
    event = make_event(organizer, total_tickets=10)
    r = client.post("/bookings", json={"event_id": event["id"], "quantity": 3}, headers=customer)
    assert r.status_code == 201
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 7


def test_overbooking_is_rejected_409(client, organizer, customer, make_event):
    event = make_event(organizer, total_tickets=5)
    r = client.post("/bookings", json={"event_id": event["id"], "quantity": 6}, headers=customer)
    assert r.status_code == 409
    # inventory untouched by the rejected request
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 5


def test_cancellation_restores_inventory(client, organizer, customer, make_event):
    event = make_event(organizer, total_tickets=10)
    booking = client.post(
        "/bookings", json={"event_id": event["id"], "quantity": 4}, headers=customer
    ).json()
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 6

    r = client.delete(f"/bookings/{booking['id']}", headers=customer)
    assert r.status_code == 204
    assert client.get(f"/events/{event['id']}").json()["available_tickets"] == 10


def test_age_gate_blocks_minor_on_restricted_event(client, organizer, customer, make_event):
    event = make_event(organizer, age_rating="A", total_tickets=10)
    r = client.post(
        "/bookings",
        json={
            "event_id": event["id"],
            "quantity": 1,
            "attendees": [{"full_name": "Kid", "age": 15}],
        },
        headers=customer,
    )
    assert r.status_code == 400
