from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime

class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: Literal["todo", "in_progress", "completed", "cancelled"] = Field(default="todo")
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="low")
    due_date: datetime | None = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    assigned_to_id: int | None 

class TaskOutFull(BaseModel):
    id: int
    title: str
    description: str | None 
    assigned_to_id: int | None 
    status: Literal["todo", "in_progress", "completed", "cancelled"]
    priority: Literal["low", "medium", "high", "urgent"]

class TaskUpdate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: Literal["todo", "in_progress", "completed", "cancelled"] = Field(default="todo")
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="low")
    due_date: datetime | None = None

class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: Literal["todo", "in_progress", "completed", "cancelled"] = Field(default="todo")
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="low")
    due_date: datetime | None = None

class TaskPatchStatus(BaseModel):
    status: Literal["todo", "in_progress", "completed", "cancelled"] = Field(default="todo")

class TaskPatchPriority(BaseModel):
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="low")