from typing import Literal, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime
from app.schemas.user import UserOut

class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: Literal["todo", "in_progress", "completed", "cancelled"] = Field(default="todo")
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="low")
    due_date: datetime | None = None
    project_id: int | None = None

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    status: Literal["todo", "in_progress", "completed", "cancelled"] = "todo"
    priority: Literal["low", "medium", "high", "urgent"] = "low"
    due_date: datetime | None = None
    project_id: int | None = None
    assigned_to_id: int | None = None
    assigned_to: UserOut | None = None

class TaskPostComment(BaseModel):
    body: str | None = None
    content: str | None = None

    @model_validator(mode="after")
    def populate_body(self):
        if not self.body and not self.content:
            raise ValueError("Comment cannot be empty")
        if not self.body:
            self.body = self.content
        return self

class TaskCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    author_id: int
    author: UserOut | None = None
    body: str
    content: str | None = None
    created_at: datetime | None = None

    @model_validator(mode="after")
    def populate_content(self):
        if not self.content:
            self.content = self.body
        return self

class TaskOutFull(TaskOut):
    comments: List[TaskCommentOut] = []

class TaskUpdate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: Literal["todo", "in_progress", "completed", "cancelled"] = Field(default="todo")
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="low")
    due_date: datetime | None = None

class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: Literal["todo", "in_progress", "completed", "cancelled"] | None = None
    priority: Literal["low", "medium", "high", "urgent"] | None = None
    due_date: datetime | None = None

class TaskPatchStatus(BaseModel):
    status: Literal["todo", "in_progress", "completed", "cancelled"] = Field(default="todo")

class TaskPatchPriority(BaseModel):
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="low")

class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: int
    user: UserOut | None = None
    description: str
    created_at: datetime
