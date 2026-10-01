from pydantic import BaseModel, Field
from app.schemas.task import TaskOut

class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)

class ProjectOut(BaseModel):
    id: int
    name: str

class ProjectOutFull(BaseModel):
    id: int
    name: str
    tasks: list[TaskOut]

class ProjectUpdate(BaseModel):
    name: str = Field(min_length=3, max_length=200)

class ProjectPatch(BaseModel):
    name: str = Field(min_length=3, max_length=200)
