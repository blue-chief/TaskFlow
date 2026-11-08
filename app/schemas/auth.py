from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm

class LoginRequest(BaseModel):
    username: str
    password: str