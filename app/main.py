from typing import Annotated
from enum import Enum
from fastapi import FastAPI, Body, Query, Path, HTTPException, Depends
from pydantic import BaseModel, Field
from app.routers import tasks
from app.routers import users
from app.routers import projects

app = FastAPI()
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(projects.router)

@app.get("/")
def home():
    return {"message" : "Welcome to TaskFlow"}

@app.get("/health/")
def health_status():
    return {"status" : "Healthy"}
