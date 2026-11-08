from html import escape 

from app.core.config import settings
from app.models.user import User
from app.services.email import EmailMessage

def _link(path: str, token:str) -> str:
    separator = "&" if "?" in path else "?"
    return f"{settings.frontend_url}{path}{separator}token={token}"

def _wrap(title: str, body_html: str) -> str:
    return (f'<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;color:#222">'
            f'<h2 style="margin-bottom:8px">{escape(title)}</h2>{body_html}'
            f'<p style="color:#888;font-size:12px;margin-top:32px">{escape(settings.app_name)}</p></div>')

def _button(url: str, label: str) -> str:
    return (f'<p><a href="{escape(url)}" style="background:#4b6bfb;color:#fff;padding:10px 18px;'
            f'border-radius:6px;text-decoration:none;display:inline-block">{escape(label)}</a></p>'
            f'<p style="font-size:12px;color:#666">Or paste this link into your browser:<br>{escape(url)}</p>')


def verification_email(user: User, raw_token: str) -> EmailMessage:
    url = _link(settings.verify_email_path, raw_token)
    return EmailMessage(
        to=user.email, subject=f"Confirm your email for {settings.app_name}",
        html=_wrap("Confirm your email",
                    f"<p>Hi {escape(user.username)}, thanks for signing up. This link is valid for 24 hours.</p>"
                    + _button(url, "Verify my email")),
        text=f"Hi {user.username},\n\nConfirm your email (valid for 24 hours):\n{url}\n",
    )


def password_reset_email(user: User, raw_token: str) -> EmailMessage:
    url = _link(settings.reset_password_path, raw_token)
    return EmailMessage(
        to=user.email, subject=f"Reset your {settings.app_name} password",
        html=_wrap("Reset your password",
                    f"<p>Hi {escape(user.username)}, we received a request to reset your password. "
                    "This link is valid for 30 minutes and can be used once.</p>" + _button(url, "Choose a new password")
                    + "<p>If you didn't ask for this, you can ignore this email — your password won't change.</p>"),
        text=(f"Hi {user.username},\n\nReset your password (valid for 30 minutes, single use):\n{url}\n\n"
              "If you didn't ask for this, ignore this email.\n"),
    )


def password_changed_email(user: User) -> EmailMessage:
    return EmailMessage(
        to=user.email, subject=f"Your {settings.app_name} password was changed",
        html=_wrap("Your password was changed",
                    f"<p>Hi {escape(user.username)}, your password was just changed and you were signed out "
                    "everywhere. If this wasn't you, reset your password immediately.</p>"),
        text=(f"Hi {user.username},\n\nYour password was just changed and you were signed out everywhere. "
              "If this wasn't you, reset your password immediately.\n"),
    )