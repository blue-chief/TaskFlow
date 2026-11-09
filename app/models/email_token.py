from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Boolean
import enum
from app.database import Base

class EmailTokenPurpose(str, enum.Enum):
    verify_email = "verify_email"
    reset_password = "reset_password"

class EmailToken(Base):
    """Single-use, expiring token emailed to a user. Only the SHA-256 hash is 
    stored - the raw value exsits in exactly one place: the email itself"""

    __tablename__ = "email_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    purpose = Column(Enum(EmailTokenPurpose), nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)