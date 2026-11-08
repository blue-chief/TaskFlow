from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from sqlalchemy.orm import Session
from app.models.user import User as UserModel
from app.schemas.auth import LoginRequest
from app.database import get_db
from app.core.security import DUMMY_PASSWORD, verify_password, create_access_token, DUMMY_HASH, hash_password
from fastapi.security import OAuth2PasswordRequestForm
from app.models.email_token import EmailTokenPurpose
from app.services.email_tokens import consume_token, issue_token, VERIFY_TTL
from app.services.email import send_email
from app.services.email_templates import verification_email
from app.services.email_templates import password_reset_email, password_changed_email
from app.services.email_tokens import RESET_TTL

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(credentials: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    user = db.query(UserModel).filter(UserModel.username == credentials.username).first()
    password_ok = verify_password(credentials.password, user.hashed_password if user else DUMMY_HASH)
    if not user or not password_ok:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail={
            "code": "email_not_verified", "message": "Please verify your email before logging in.",
        })
    token = create_access_token(user.id, user.token_version)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/verify-email")
def verify_email(payload: dict, db: Annotated[Session, Depends(get_db)]):
    user = consume_token(db, payload["token"], EmailTokenPurpose.verify_email)
    if not user:
        raise HTTPException(status_code=400, detail="This verification link is invalid or has expired.")
    user.is_verified = True
    db.commit()
    return {"message": "Email verified. You can now log in."}

@router.post("/resend-verification", status_code=202)
def resend_verification(payload: dict, background_tasks: BackgroundTasks, db: Annotated[Session, Depends(get_db)]):
    user = db.query(UserModel).filter(UserModel.email == payload["email"]).first()
    if user and not user.is_verified:
        raw_token = issue_token(db, user, EmailTokenPurpose.verify_email, VERIFY_TTL)
        if raw_token:
            db.commit()
            background_tasks.add_task(send_email, verification_email(user, raw_token))
    return {"message": "If that email address is registered, we've sent instructions to it."}

GENERIC_MESSAGE = {"message": "If that email address is registered, we've sent instructions to it."}

@router.post("/forgot-password", status_code=202)
def forgot_password(payload: dict, background_tasks: BackgroundTasks, db: Annotated[Session, Depends(get_db)]):
    user = db.query(UserModel).filter(UserModel.email == payload["email"]).first()
    if user:
        raw_token = issue_token(db, user, EmailTokenPurpose.reset_password, RESET_TTL)
        if raw_token:
            db.commit()
            background_tasks.add_task(send_email, password_reset_email(user, raw_token))
    return GENERIC_MESSAGE  # same response whether or not the email exists — never confirm which emails are registered

@router.post("/reset-password")
def reset_password(payload: dict, background_tasks: BackgroundTasks, db: Annotated[Session, Depends(get_db)]):
    user = consume_token(db, payload["token"], EmailTokenPurpose.reset_password)
    if not user:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")
    user.hashed_password = hash_password(payload["new_password"])
    user.token_version += 1  # every JWT issued before this moment is now rejected
    user.is_verified = True
    db.commit()
    background_tasks.add_task(send_email, password_changed_email(user))
    return {"message": "Password updated. Please log in with your new password."}