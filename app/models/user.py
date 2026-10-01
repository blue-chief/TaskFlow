from app.database import Base

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    d_tasks = relationship("Task", back_populates="d_user")
    owned_projects = relationship("Project", back_populates="owner")
    memberships = relationship("ProjectMember", back_populates="user")