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


def template(title, lines):
    text = title + "\n\n" + "\n".join(lines)
    html = (
        '<div style="font-family:Arial,sans-serif;background:#fff7f7;padding:28px;color:#222">'
        '<div style="max-width:560px;margin:auto;background:white;border-radius:12px;padding:28px">'
        '<p style="color:#df2947;font-weight:bold">JTickets</p>'
        f'<h1 style="font-size:24px">{escape(title)}</h1>'
        + "".join(f'<p style="line-height:1.6">{escape(str(line))}</p>' for line in lines)
        + '<p style="font-size:12px;color:#666">Keep this email for your records.</p></div></div>'
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
