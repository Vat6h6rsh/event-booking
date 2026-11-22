"""Transactional email transports and shared, escaped HTML templates."""
import logging
import os
import smtplib
import ssl
from datetime import timedelta, timezone
from email.message import EmailMessage
from html import escape

import httpx

logger = logging.getLogger("jtickets.email")
IST = timezone(timedelta(hours=5, minutes=30))


class EmailDeliveryError(RuntimeError):
    """Only sanitized transport/configuration errors may be persisted in jobs."""


def ist_date(value):
    if value.tzinfo is None: value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")


_RED, _YELLOW, _CREAM, _INK, _NIGHT = "#d7263d", "#ffc93c", "#fff4dc", "#2b1d0e", "#1b1035"
_MONO = "'Courier New',Courier,monospace"
_ASSETS = os.getenv("EMAIL_ASSET_BASE", "https://event-booking-nine-blue.vercel.app").rstrip("/")


def _marquee():
    return (
        f'<img src="{_ASSETS}/images/email/marquee.gif" width="600" alt="JTICKETS" '
        'style="display:block;width:100%;max-width:600px;height:auto;image-rendering:pixelated;border:0">'
    )


def template(title, lines):
    """Generic notice (used for event-update emails) in the same pixel carnival look."""
    text = title + "\n\n" + "\n".join(lines)
    html = (
        f'<div style="margin:0;padding:24px 10px;background:{_NIGHT}">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="max-width:600px;margin:auto;font-family:{_MONO}">'
        f'<tr><td style="padding:0 0 18px">{_marquee()}</td></tr>'
        f'<tr><td style="padding:0 8px 18px 2px"><div style="background:{_CREAM};border:4px solid {_INK};'
        f'box-shadow:6px 6px 0 {_RED};padding:18px 20px;color:{_INK}">'
        f'<div style="font-size:11px;font-weight:bold;letter-spacing:3px;color:{_RED}">&#9733; NOTICE &#9733;</div>'
        f'<h1 style="font-size:20px;margin:10px 0 12px;text-transform:uppercase">{escape(title)}</h1>'
        + "".join(f'<p style="font-size:13px;line-height:1.6;margin:0 0 8px">&#9656; {escape(str(line))}</p>'
                  for line in lines)
        + '</div></td></tr>'
        f'<tr><td style="text-align:center;font-size:11px;color:{_CREAM}">Keep this email for your records.</td></tr>'
        '</table></div>'
    )
    return html, text


def _ticket_stub(*, event, when, venue, tier, attendee, seat, code, number, count):
    """One pixel-style carnival ticket: main body | perforation | tear-off ADMIT ONE stub."""
    e = lambda v: escape(str(v))
    seat_html = f" &middot; SEAT <b>{e(seat)}</b>" if seat else ""
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="border-collapse:collapse;margin:0 0 18px;background:{_CREAM};'
        f'border:4px solid {_INK};box-shadow:6px 6px 0 {_RED}">'
        '<tr>'
        f'<td style="padding:16px 18px;vertical-align:top;font-family:{_MONO};color:{_INK}">'
        f'<div style="font-size:11px;font-weight:bold;letter-spacing:3px;color:{_RED}">'
        f'&#9733; TICKET {number:02d}/{count:02d} &#9733;</div>'
        f'<div style="font-size:20px;font-weight:bold;margin:10px 0 8px;line-height:1.2;text-transform:uppercase">{e(event)}</div>'
        f'<div style="font-size:13px;line-height:1.7">&#9656; {e(when)}<br>&#9656; {e(venue)}</div>'
        f'<div style="font-size:12px;line-height:1.6;margin-top:10px;padding-top:8px;border-top:2px dotted {_INK};text-transform:uppercase">'
        f'GUEST <b>{e(attendee)}</b> &middot; {e(tier)}{seat_html}</div>'
        '</td>'
        f'<td width="1" style="border-left:4px dashed {_INK};padding:0;font-size:0">&nbsp;</td>'
        f'<td width="128" style="padding:12px 10px;text-align:center;vertical-align:middle;'
        f'background:{_YELLOW};font-family:{_MONO};color:{_INK}">'
        '<div style="font-size:11px;font-weight:bold;letter-spacing:3px">ADMIT</div>'
        f'<div style="font-size:40px;line-height:1;font-weight:bold;color:{_RED}">1</div>'
        f'<div style="margin-top:8px;padding:6px 4px;background:#ffffff;border:3px solid {_INK};'
        'font-size:12px;font-weight:bold;letter-spacing:1px;line-height:1.3;word-break:break-all">'
        f'{e(code)}</div>'
        '<div style="font-size:9px;margin-top:6px;letter-spacing:1px">SHOW AT GATE</div>'
        '</td></tr></table>'
    )


def ticket_template(*, event, when, venue, tier, quantity, total, booking_id, attendees):
    """Booking confirmation styled as a strip of pixel-art carnival tickets.

    ``attendees`` is a list of (full_name, seat_label | None, ticket_code).
    Returns (html, text); every interpolated value is HTML-escaped.
    """
    count = len(attendees) or quantity
    text = "\n".join([
        "Your booking is confirmed", "",
        f"Event: {event}", f"Date: {when}", f"Venue: {venue}", f"Tier: {tier}",
        f"Quantity: {quantity}", f"Total: ₹{total}", f"Booking ID: {booking_id}", "",
        "Tickets:",
        *[f"  {i}. {name}{f' (seat {seat})' if seat else ''} - {code}"
          for i, (name, seat, code) in enumerate(attendees, 1)],
        "", "Show the ticket code at the entry gate.",
    ])
    stubs = "".join(
        _ticket_stub(event=event, when=when, venue=venue, tier=tier, attendee=name,
                     seat=seat, code=code, number=i, count=count)
        for i, (name, seat, code) in enumerate(attendees, 1)
    )
    e = lambda v: escape(str(v))
    row = lambda k, v: (
        f'<tr><td style="padding:5px 0">{k}</td>'
        f'<td style="padding:5px 0;text-align:right;font-weight:bold">{v}</td></tr>'
    )
    html = (
        f'<div style="margin:0;padding:24px 10px;background:{_NIGHT}">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="max-width:600px;margin:auto;background:{_NIGHT};font-family:{_MONO}">'
        f'<tr><td style="padding:0 0 18px">{_marquee()}</td></tr>'
        f'<tr><td style="padding:0 6px 18px;text-align:center;color:{_YELLOW}">'
        '<div style="font-size:22px;font-weight:bold;letter-spacing:2px">STEP RIGHT UP &mdash; YOU&rsquo;RE IN!</div>'
        f'<div style="font-size:13px;color:{_CREAM};margin-top:6px">Booking confirmed. Your tickets are below.</div>'
        '</td></tr>'
        f'<tr><td style="padding:0 8px 0 2px">{stubs}</td></tr>'
        f'<tr><td style="padding:4px 8px 18px 2px">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:{_YELLOW};border:4px solid {_INK};box-shadow:6px 6px 0 {_RED};'
        f'font-size:13px;color:{_INK}"><tr><td style="padding:12px 16px">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-family:inherit;font-size:13px">'
        + row("BOOKING", f"#{e(booking_id)}") + row("TICKETS", e(quantity)) + row("TIER", e(tier).upper())
        + f'<tr><td style="padding:8px 0 0;border-top:3px solid {_INK};font-size:15px;font-weight:bold">TOTAL PAID</td>'
          f'<td style="padding:8px 0 0;border-top:3px solid {_INK};text-align:right;font-size:20px;font-weight:bold;color:{_RED}">'
          f'&#8377;{e(total)}</td></tr>'
        '</table></td></tr></table></td></tr>'
        f'<tr><td style="padding:0 6px;text-align:center;font-size:11px;line-height:1.6;color:{_CREAM}">'
        'Show the code on each ticket at the gate. Keep this email for your records.<br>'
        f'<span style="color:{_YELLOW}">&#9632;&#9633;&#9632;&#9633;&#9632; JTICKETS &#9632;&#9633;&#9632;&#9633;&#9632;</span></td></tr>'
        '</table></div>'
    )
    return html, text


def send_email(to, subject, html, text):
    """Raise a sanitized error on failure; the durable outbox owns retries."""
    domains = {s.strip().lower() for s in os.getenv(
        "EMAIL_SUPPRESS_DOMAINS", "loadtest.jtickets.dev,example.com"
    ).split(",") if s.strip()}
    if to.rsplit("@", 1)[-1].lower() in domains:
        logger.info("[EMAIL] suppressed recipient domain")
        return
    provider = os.getenv("EMAIL_PROVIDER", "console").lower()
    if provider == "console":
        logger.info("[EMAIL] console | %s\n%s", subject, text)
        return
    sender = os.getenv("EMAIL_FROM", "")
    sender_name = os.getenv("EMAIL_FROM_NAME", "JTickets")
    if not sender: raise EmailDeliveryError("EMAIL_FROM is required for email delivery")
    if provider == "brevo":
        key = os.getenv("BREVO_API_KEY", "")
        if not key: raise EmailDeliveryError("BREVO_API_KEY is required for Brevo delivery")
        try:
            response = httpx.post(
                "https://api.brevo.com/v3/smtp/email", headers={"api-key": key},
                json={"sender": {"name": sender_name, "email": sender},
                      "to": [{"email": to}], "subject": subject,
                      "htmlContent": html, "textContent": text}, timeout=10,
            )
        except httpx.HTTPError:
            raise EmailDeliveryError("Brevo email transport failed") from None
        if not 200 <= response.status_code < 300:
            raise EmailDeliveryError(f"Brevo email rejected (HTTP {response.status_code})")
    elif provider == "smtp":
        message = EmailMessage()
        message["From"] = f"{sender_name} <{sender}>"
        message["To"], message["Subject"] = to, subject
        message.set_content(text)
        message.add_alternative(html, subtype="html")
        try:
            with smtplib.SMTP(os.getenv("SMTP_HOST", "localhost"), int(os.getenv("SMTP_PORT", "587")), timeout=10) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                if os.getenv("SMTP_USER"):
                    smtp.login(os.environ["SMTP_USER"], os.getenv("SMTP_PASSWORD", ""))
                if smtp.send_message(message): raise EmailDeliveryError("SMTP recipient rejected")
        except (smtplib.SMTPException, OSError):
            raise EmailDeliveryError("SMTP email delivery failed") from None
    else:
        raise EmailDeliveryError("EMAIL_PROVIDER must be brevo, smtp or console")
