from pydantic import BaseModel, Field, ConfigDict
from app.schemas.task import TaskOut
from app.schemas.project_member import ProjectMemberOut

class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)

class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int

class ProjectOutFull(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int
    tasks: list[TaskOut] = []
    members: list[ProjectMemberOut] = []

class ProjectUpdate(BaseModel):
    name: str = Field(min_length=3, max_length=200)

class ProjectPatch(BaseModel):
    name: str = Field(min_length=3, max_length=200)

