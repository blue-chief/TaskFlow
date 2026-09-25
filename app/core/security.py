from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

DUMMY_PASSWORD = "themostfakepasswordever123"

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain:str, hashed:str) -> bool:
    return password_hash.verify(plain, hashed)

def get_current_user() -> dict:
    return {"id":1, "username":"temp_user"}