from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    d_user = relationship("User", back_populates="d_tasks")
    project = relationship("Project", back_populates="tasks")