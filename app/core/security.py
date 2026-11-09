from typing import Annotated
from pwdlib import PasswordHash
import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User as UserModel
from app.database import get_db
from jwt.exceptions import InvalidTokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
password_hash = PasswordHash.recommended()

DUMMY_PASSWORD = "themostfakepasswordever123"

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain:str, hashed:str) -> bool:
    return password_hash.verify(plain, hashed)

def create_access_token(user_id: int, token_version: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {"sub": str(user_id), "tv": token_version, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Annotated [Session, Depends(get_db)],
) -> UserModel:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"]
        )

        user_id = int(payload["sub"])

    except (InvalidTokenError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if payload.get("tv") != user.token_version:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

def get_verified_user(current_user: Annotated[UserModel, Depends(get_current_user)]) -> UserModel:
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail={
            "code": "email_not_verified", "message": "Please verify your email address first.",
        })
    return current_user

DUMMY_HASH = hash_password("not-a-real-password-just-for-timing")