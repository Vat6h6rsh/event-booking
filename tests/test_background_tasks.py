"""
The two required background tasks. Each asserts BOTH observable effects:
the console log the exercise asks for (via caplog) AND the in-app notification
row that makes the alert visible in the UI.

Note: FastAPI/Starlette's TestClient runs background tasks to completion before
returning the response, so their effects are already present here.
"""
import logging


def test_task1_booking_confirmation_fires(client, organizer, customer, make_event, caplog):
    event = make_event(organizer)
    with caplog.at_level(logging.INFO, logger="jtickets.notifications"):
        r = client.post("/bookings", json={"event_id": event["id"], "quantity": 1}, headers=customer)
        assert r.status_code == 201

    # 1) console log fired
    assert "[EMAIL] Booking confirmation" in caplog.text
    # 2) in-app notification recorded for the booking customer
    notes = client.get("/notifications", headers=customer).json()
    assert any(n["type"] == "booking_confirmed" for n in notes)


def test_task2_event_update_notifies_booked_customer(client, organizer, customer, make_event, caplog):
    event = make_event(organizer)
    client.post("/bookings", json={"event_id": event["id"], "quantity": 1}, headers=customer)

    with caplog.at_level(logging.INFO, logger="jtickets.notifications"):
        r = client.put(f"/events/{event['id']}", json={"venue": "New Arena"}, headers=organizer)
        assert r.status_code == 200

    # 1) console log fired
    assert "[NOTIFY]" in caplog.text
    # 2) the customer who booked has an event_updated notification for this event
    notes = client.get("/notifications", headers=customer).json()
    assert any(n["type"] == "event_updated" and n["event_id"] == event["id"] for n in notes)


def test_task2_does_not_notify_customers_who_did_not_book(client, organizer, customer, new_user, make_event):
    event = make_event(organizer)
    client.post("/bookings", json={"event_id": event["id"], "quantity": 1}, headers=customer)

    bystander = new_user("customer")  # never booked this event
    client.put(f"/events/{event['id']}", json={"venue": "New Arena"}, headers=organizer)

    notes = client.get("/notifications", headers=bystander).json()
    assert all(n["type"] != "event_updated" for n in notes)
