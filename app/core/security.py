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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
password_hash = PasswordHash.recommended()

DUMMY_PASSWORD = "themostfakepasswordever123"

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain:str, hashed:str) -> bool:
    return password_hash.verify(plain, hashed)

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Annotated [Session, Depends(get_db)],
) -> UserModel:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except jwt.PyJWKError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user