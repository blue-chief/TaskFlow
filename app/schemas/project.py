from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    id: str
    name: str = Field(min_length=3, max_length=200)

class ProjectOut(BaseModel):
    id: str
    name: str

class ProjectUpdate(BaseModel):
    name: str = Field(min_length=3, max_length=200)

class ProjectPatch(BaseModel):
    name: str = Field(min_length=3, max_length=200)
