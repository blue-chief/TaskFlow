from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=8)

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    class Config:
        from_attributes = True