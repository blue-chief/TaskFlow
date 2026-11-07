import logging

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestLogMiddleware
from app.core.rate_limit import limiter, rate_limit_handler
from app.database import SessionLocal
from app.routers import tasks, users, projects, auth, project_members

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    #Docs are handy in development; in production they only help an attacker map your API.
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None,
    openapi_url=None if settings.environment == "production" else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins, #explicit list, never "*" once real users log in
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(auth.router)
app.include_router(project_members.router)

@app.get("/")
def home():
    return {"message" : "Welcome to TaskFlow"}

@app.get("/health")
def health_status():
    """Liveness - 'the process is up'. Cheap; doesn't touch the database"""
    return {"status" : "Healthy"}

@app.get("/health/ready")
def ready(response: Response):
    """Readiness - 'the process can actually serve traffic', i.e the database answers"""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness check failed")
        response.status_code = 503
        return {"status": "unavailable"}
    return{"status":"readyS"}
