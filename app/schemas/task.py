from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None 
    assigned_to_id: int 

class TaskUpdate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)