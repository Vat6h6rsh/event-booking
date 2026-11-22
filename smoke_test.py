"""End-to-end smoke test for the Event Booking API."""
import os
import sys
import uuid

import httpx

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
RUN = uuid.uuid4().hex[:8]  # unique emails so the script can be re-run against the same DB
ORG_EMAIL = f"org-{RUN}@example.com"
FAN_EMAIL = f"fan-{RUN}@example.com"


def check(label: str, r: httpx.Response, expected: int) -> dict:
    ok = r.status_code == expected
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {label} -> HTTP {r.status_code}  {r.text[:120]}")
    if not ok:
        sys.exit(1)
    return r.json() if r.content else {}


# 1. Signup organizer
r = httpx.post(f"{BASE}/signup", json={"email": ORG_EMAIL, "password": "secret123", "role": "organizer"})
check("Signup organizer", r, 201)

# 2. Login organizer
r = httpx.post(f"{BASE}/login", data={"username": ORG_EMAIL, "password": "secret123"})
data = check("Login organizer", r, 200)
org_hdr = {"Authorization": f"Bearer {data['access_token']}"}

# 3. Create event
r = httpx.post(
    f"{BASE}/events",
    json={"name": "Rock Night", "venue": "Arena", "event_date": "2026-12-01T20:00:00", "total_tickets": 10},
    headers=org_hdr,
)
data = check("Create event", r, 201)
event_id = data["id"]

# 4. List events (public, no auth)
r = httpx.get(f"{BASE}/events")
check("List events (no auth)", r, 200)

# 5. Signup customer
r = httpx.post(f"{BASE}/signup", json={"email": FAN_EMAIL, "password": "secret123", "role": "customer"})
check("Signup customer", r, 201)

# 6. Login customer
r = httpx.post(f"{BASE}/login", data={"username": FAN_EMAIL, "password": "secret123"})
data = check("Login customer", r, 200)
cust_hdr = {"Authorization": f"Bearer {data['access_token']}"}

# 7. Customer tries to create event -> must get 403
r = httpx.post(
    f"{BASE}/events",
    json={"name": "Fake", "venue": "X", "event_date": "2026-12-01T20:00:00", "total_tickets": 5},
    headers=cust_hdr,
)
check("Customer POST /events (expect 403)", r, 403)

# 8. Book tickets -> Background Task 1 fires a confirmation log
r = httpx.post(f"{BASE}/bookings", json={"event_id": event_id, "quantity": 3}, headers=cust_hdr)
check("Book 3 tickets", r, 201)

# 9. Verify available_tickets decremented
r = httpx.get(f"{BASE}/events/{event_id}")
data = check("Event still 7 tickets left", r, 200)
assert data["available_tickets"] == 7, f"Expected 7, got {data['available_tickets']}"

# 10. Overbook -> 409 (8 > 7 remaining; quantity itself must stay within the 1-10 schema limit)
r = httpx.post(f"{BASE}/bookings", json={"event_id": event_id, "quantity": 8}, headers=cust_hdr)
check("Overbook (expect 409)", r, 409)

# 11. Organizer updates event -> Background Task 2 fires notify log
r = httpx.put(f"{BASE}/events/{event_id}", json={"venue": "New Venue"}, headers=org_hdr)
data = check("Update event venue", r, 200)
assert data["venue"] == "New Venue", f"Expected 'New Venue', got {data['venue']}"

# 12. My bookings
r = httpx.get(f"{BASE}/bookings", headers=cust_hdr)
data = check("My bookings", r, 200)
assert len(data) == 1

# 13. Organizer cannot hit customer-only route -> 403
r = httpx.get(f"{BASE}/bookings", headers=org_hdr)
check("Organizer GET /bookings (expect 403)", r, 403)

# 14. Unauthenticated request -> 401
r = httpx.post(f"{BASE}/bookings", json={"event_id": event_id, "quantity": 1})
check("No token POST /bookings (expect 401)", r, 401)

print()
print("=" * 50)
print("  ALL TESTS PASSED")
print("=" * 50)
