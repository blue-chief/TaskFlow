from typing import Literal
from pydantic import BaseModel, Field

class ProjectMemberCreate(BaseModel):
    user_id: int

class ProjectMemberOut(BaseModel):
    user_id: int
    role: str