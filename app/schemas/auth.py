from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm

class LoginRequest(OAuth2PasswordRequestForm):
    username: str
    password: str