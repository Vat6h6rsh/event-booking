from fastapi import APIRouter

router = APIRouter(prefix="/legal", tags=["legal"])

TERMS = """\
# Terms of Use  —  Jtickets

Last updated: June 2026

1. **Eligibility** — You must be at least 13 years old to use this service.
2. **Account security** — You are responsible for keeping your credentials safe.
3. **Bookings** — Bookings are subject to availability. Prices shown are inclusive of all fees.
4. **Age-restricted events** — Events rated "A" or "18+" may only be booked for attendees aged 18+.
5. **Cancellations & refunds** — Each organiser sets their own refund policy. Jtickets is not liable for organiser cancellations.
6. **Prohibited conduct** — Scalping, fraudulent bookings, and harassment are strictly prohibited and may result in account termination.
7. **Intellectual property** — All platform content is owned by Jtickets or its licensors.
8. **Limitation of liability** — Jtickets is not liable for indirect, consequential, or incidental damages.
9. **Governing law** — These terms are governed by the laws of India.
10. **Changes** — We may update these terms at any time. Continued use constitutes acceptance.

Contact: legal@jtickets.in
"""

PRIVACY = """\
# Privacy Policy  —  Jtickets

Last updated: June 2026

**What we collect**
- Account data: email, name, phone, date of birth.
- Booking data: events booked, attendee names, seat labels, ticket codes.
- Usage data: pages visited, timestamps (no third-party analytics).

**How we use it**
- To process and confirm bookings.
- To send transactional emails (confirmation, event updates).
- To enforce age restrictions on applicable events.

**Sharing**
- We share your name and booking reference with the event organiser for entry verification only.
- We do not sell your data.

**Security**
- Passwords are hashed with bcrypt. Sessions use signed JWT tokens.
- Images are stored on Cloudflare R2 with private-by-default access.

**Your rights**
- Request a copy of your data: privacy@jtickets.in
- Request account & data deletion at any time.
- Opt out of non-transactional emails via account settings.

**Cookies**
- We use localStorage for session tokens. No third-party tracking cookies.

Contact: privacy@jtickets.in
"""

@router.get("/terms")
def terms(): return {"type": "terms", "content": TERMS}

@router.get("/privacy")
def privacy(): return {"type": "privacy", "content": PRIVACY}
