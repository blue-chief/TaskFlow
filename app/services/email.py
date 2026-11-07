import asyncio
import logging
import uuid
from dataclasses import dataclass
from email.utils import parseaddr

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"
BREVO_URL= "https://api.brevo.com/v3/smtp/email"
MAX_ATTEMPTS = 3
RETRY_BASE_DELAY =  0.5 # seconds; doubles after each failed atttempt
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

@dataclass
class EmailMessage:
    to: str
    subject: str
    html: str
    text: str

class EmailSendError(Exception):
    pass

outbox: list[EmailMessage] = [] # the "memory" backend appends here - tests read it

def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=10.0)

async def _post_with_retry(url: str, *, headers: dict, payload: dict) -> None:
    last_error: Exception | None = None
    async with _client as client:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = await client.post(url, headers=headers, json=payload)
            except httpx.TransportError as exc:
                last_error = exc
            else:
                if response.status_code < 400:
                    return
                if response.status_code not in RETRYABLE_STATUS:
                    raise EmailSendError(f"{response.status_code}: {response.text[:300]}")
                last_error = EmailSendError(f"{response.status_code}: {response.text[:300]}")
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(RETRY_BASE_DELAY * 2 ** (attempt - 1))
    raise EmailSendError(f"gave up after {MAX_ATTEMPTS} attempts: {last_error}")

async def _send_resend(message: EmailMessage) -> None:
    await _post_with_retry(
        RESEND_URL,
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Idempotency-Key": str(uuid.uuid4()),
        },
        payload = {"from": settings.email_from, "to": [message.to], "subject": message.subject,
                   "html": message.html, "text": message.text,
                   }
    )

async def _send_brevo(message: EmailMessage) -> None:
    sender_name, sender_email = parseaddr(settings.email_from)
    await _post_with_retry(
        BREVO_URL,
        headers={"api-key": settings.brevo_api_key, "accept":"application/json"},
        payload={"sender": {"name": sender_name, "email": sender_email},
                 "to":[{"email": message.to}], "subject": message.subject, "htmlContent": message.html},
    )

async def send_email(message: EmailMessage) -> None:
    """Send one email. Never raises: this runs inside a FastAPI BackgroundTask,
    after the HTTP response has already gone out — there's nobody left to catch
    an exception at that point, so a failure gets logged instead of crashing anything."""

    try:
        if settings.email_backend == "console":
            logger.info("EMAIL to=%s subject=%r\n%s", message.to, message.subject, message.text)
        elif settings.email_backend == "memory":
            outbox.append(message)
        elif settings.email_backend == "resend":
            await _send_resend(message)
        elif settings.email_backend == "brevo":
            await _send_brevo(message)
    except Exception:
        logger.exception("Could not send email (subject=%r) to %s", message.subject, message.to)