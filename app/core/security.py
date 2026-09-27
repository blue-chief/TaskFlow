from pwdlib import PasswordHash
import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

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

def get_current_user() -> dict:
    return {"id":1, "username":"temp_user"}