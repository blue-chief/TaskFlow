import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.email_token import EmailToken, EmailTokenPurpose
from app.models.user import User

VERIFY_TTL = timedelta(hours=24)
RESET_TTL = timedelta(minutes=30)
RESEND_COOLDOWN = timedelta(seconds=60)


def _hash(raw_token: str) -> str:
    # SHA-256 is correct here, NOT Argon2 — this token is already 256 bits of
    # randomness (nothing to brute-force), unlike a human-chosen password,
    # which is why passwords specifically need the slow, salted hashing.
    return hashlib.sha256(raw_token.encode()).hexdigest()


def issue_token(db: Session, user: User, purpose: EmailTokenPurpose, ttl: timedelta,
                 cooldown: timedelta = RESEND_COOLDOWN) -> str | None:
    """Create a fresh token, return the RAW value (goes in the email). Returns
    None — and the caller should quietly do nothing — if a token for this
    user+purpose was already issued less than `cooldown` ago."""
    now = datetime.now(timezone.utc)
    latest = db.scalar(select(func.max(EmailToken.created_at)).where(
        EmailToken.user_id == user.id, EmailToken.purpose == purpose))
    if latest is not None and now - latest < cooldown:
        return None

    # Only the newest link should ever work — drop any older unused ones first.
    db.execute(delete(EmailToken).where(EmailToken.user_id == user.id, EmailToken.purpose == purpose,
                                          EmailToken.used_at.is_(None)))

    raw_token = secrets.token_urlsafe(32)
    db.add(EmailToken(user_id=user.id, purpose=purpose, token_hash=_hash(raw_token),
                       created_at=now, expires_at=now + ttl))
    db.flush()
    return raw_token


def consume_token(db: Session, raw_token: str, purpose: EmailTokenPurpose) -> User | None:
    """Validate a token and mark it used. Returns the owner, or None if the
    token is unknown, wrong-purpose, already used, or expired. The caller
    commits. `with_for_update()` locks the row so two simultaneous requests
    carrying the same link can't both succeed."""
    row = db.scalar(select(EmailToken).where(EmailToken.token_hash == _hash(raw_token),
                     EmailToken.purpose == purpose).with_for_update())
    now = datetime.now(timezone.utc)
    if row is None or row.used_at is not None or row.expires_at < now:
        return None
    row.used_at = now
    return db.get(User, row.user_id)
