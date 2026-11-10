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
    raw_token = payload.get("token", "").strip() if isinstance(payload, dict) else ""
    user = consume_token(db, raw_token, EmailTokenPurpose.verify_email)
    if not user:
        raise HTTPException(status_code=400, detail="This verification link is invalid or has expired.")
    user.is_verified = True
    db.commit()
    return {"message": "Email verified. You can now log in."}

@router.get("/verify-email")
def verify_email_get(token: str, db: Annotated[Session, Depends(get_db)]):
    from fastapi.responses import HTMLResponse
    from app.core.config import settings

    login_url = f"{settings.frontend_url}/login.html" if settings.frontend_url else "/frontend/login.html"
    resend_url = f"{settings.frontend_url}/resend-verification.html" if settings.frontend_url else "/frontend/resend-verification.html"

    user = consume_token(db, token.strip(), EmailTokenPurpose.verify_email)
    if not user:
        error_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Verification Link Invalid — TaskFlow</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ background: #F8FAFC; color: #0F172A; font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 1.5rem; }}
        .card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 2.5rem 2rem; max-width: 440px; width: 100%; text-align: center; box-shadow: 0 10px 25px -5px rgba(15,23,42,0.08); }}
        .icon {{ font-size: 2.75rem; margin-bottom: 0.75rem; }}
        h1 {{ color: #BE123C; margin: 0 0 0.5rem; font-size: 1.5rem; font-weight: 800; }}
        p {{ color: #475569; line-height: 1.6; margin: 0 0 1.5rem; font-size: 0.95rem; }}
        .btn {{ display: inline-block; background: #4F46E5; color: #FFFFFF; font-weight: 600; text-decoration: none; padding: 0.75rem 1.5rem; border-radius: 10px; font-size: 0.9rem; transition: opacity 0.15s; }}
        .btn:hover {{ opacity: 0.9; }}
        .btn-secondary {{ background: #FFFFFF; border: 1px solid #E2E8F0; color: #334155; margin-left: 0.5rem; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">⚠️</div>
        <h1>Link Invalid or Expired</h1>
        <p>This verification link is invalid, has expired, or has already been used to verify an account.</p>
        <div>
            <a href="{login_url}" class="btn">Go to Log in</a>
            <a href="{resend_url}" class="btn btn-secondary">Request New Link</a>
        </div>
    </div>
</body>
</html>"""
        return HTMLResponse(content=error_html, status_code=400)

    user.is_verified = True
    db.commit()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Email Verified — TaskFlow</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="4;url={login_url}">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ background: #F8FAFC; color: #0F172A; font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 1.5rem; }}
        .card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 2.5rem 2rem; max-width: 440px; width: 100%; text-align: center; box-shadow: 0 10px 25px -5px rgba(15,23,42,0.08); }}
        .icon {{ font-size: 2.75rem; margin-bottom: 0.75rem; }}
        h1 {{ color: #047857; margin: 0 0 0.5rem; font-size: 1.6rem; font-weight: 800; }}
        p {{ color: #475569; line-height: 1.6; font-size: 0.95rem; }}
        .btn {{ display: inline-block; background: #4F46E5; color: #FFFFFF; font-weight: 600; text-decoration: none; padding: 0.75rem 1.5rem; border-radius: 10px; font-size: 0.9rem; margin-top: 1.25rem; transition: opacity 0.15s; }}
        .btn:hover {{ opacity: 0.9; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">✅</div>
        <h1>Email Verified!</h1>
        <p>Your email for <strong>{user.username}</strong> has been successfully verified.</p>
        <p style="font-size: 0.85rem; color: #64748B;">Redirecting to login in 4 seconds...</p>
        <a href="{login_url}" class="btn">Go to Log in &rarr;</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


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