from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class ProjectMemberCreate(BaseModel):
    user_id: int | None = None
    username: str | None = None

class ProjectMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    project_id: int | None = None
    user_id: int
    username: str | None = None
    role: str
