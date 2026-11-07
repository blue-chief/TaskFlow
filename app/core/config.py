from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://user:password@localhost:5432/taskflow"
    secret_key: str = "change-me"
    environment: Literal["development", "test", "production"] = "development"
    app_name: str = "TaskFlow"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://127.0.0.1:5500", "http://localhost:5500"]
    frontend_url: str = "http://localhost:5500"
    verify_email_path: str = "/verify-email.html"
    reset_password_path: str = "/reset-password.html"
    email_backend: str = "console" # "console" / "memory" / "resend" / "brevo"
    email_from: str = "TaskFlow <onboarding@resend.dev>"
    resend_api_key: str = ""
    brevo_api_key: str = ""

    @model_validator(mode="after")
    def refuse_unsafe_configuration(self):
        if self.environment == "production":
            if self.secret_key == "change-me" or len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be a random value of 32+ characters in production")
            
            if self.email_backend in ("console", "memory"):
                raise ValueError("EMAIL_BACKEND must be 'resend' or 'brevo' in production")
        if self.email_backend == "resend" and not self.resend_api_key:
            raise ValueError("RESEND_API_KEY is required when EMAIL_BACKEND=resend")
        if self.email_backend == "brevo" and not self.brevo_api_key:
            raise ValueError("RESEND_API_KEY is required when EMAIL_BACKEND=brevo")
        return self

settings = Settings()