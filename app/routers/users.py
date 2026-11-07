from typing import Annotated
from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks
from datetime import timedelta

from app.schemas.user import UserCreate, UserOut
from app.models.user import User as UserModel
from app.database import get_db
from sqlalchemy.orm import Session
from app.core.security import hash_password, get_current_user
from app.models.email_token import EmailTokenPurpose
from app.services.email import send_email
from app.services.email_templates import verification_email
from app.services.email_tokens import issue_token, VERIFY_TTL

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, background_tasks: BackgroundTasks, db: Annotated[Session, Depends(get_db)]):
    existing = db.query(UserModel).filter(UserModel.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    new_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.flush()

    raw_token = issue_token(db, new_user, EmailTokenPurpose.verify_email, VERIFY_TTL, cooldown=timedelta(0))
    db.commit()
    background_tasks.add_task(send_email, verification_email(new_user, raw_token))
    db.refresh(new_user)
    return new_user

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: Annotated[UserModel, Depends(get_current_user)]):
    return current_user