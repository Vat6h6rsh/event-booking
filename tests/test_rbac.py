"""Role-based access control — the core requirement: 'API access controlled by role'."""


def test_unauthenticated_request_is_401(client):
    r = client.post("/bookings", json={"event_id": 1, "quantity": 1})
    assert r.status_code == 401


def test_customer_cannot_create_event_403(client, customer):
    r = client.post(
        "/events",
        json={"name": "X", "venue": "Y", "event_date": "2099-01-01T00:00:00", "total_tickets": 5},
        headers=customer,
    )
    assert r.status_code == 403


def test_organizer_cannot_list_customer_bookings_403(client, organizer):
    r = client.get("/bookings", headers=organizer)
    assert r.status_code == 403


def test_organizer_cannot_edit_another_organizers_event_403(client, new_user, make_event):
    owner = new_user("organizer")
    other = new_user("organizer")
    event = make_event(owner)
    r = client.put(f"/events/{event['id']}", json={"venue": "Hijacked"}, headers=other)
    assert r.status_code == 403
