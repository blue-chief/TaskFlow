from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends

from sqlalchemy.orm import Session
from app.models.user import User as UserModel
from app.schemas.auth import LoginRequest
from app.database import get_db
from app.core.security import DUMMY_PASSWORD, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(credentials: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[Session, Depends(get_db)]):
    user = db.query(UserModel).filter(UserModel.username == credentials.username).first()
    if not user:
        verify_password(DUMMY_PASSWORD)
        raise HTTPException(status_code=401, detail="Invalid Username or Password")
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Username or Password")
    token = create_access_token(user.id)
    return{"access_token": token, "token_type": "bearer"}