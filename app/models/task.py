from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import Enum as SAEnum
import enum
from sqlalchemy.orm import relationship
from app.database import Base

class TaskStatusEnum(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(SAEnum(TaskStatusEnum), default=TaskStatusEnum.todo, nullable=False)

    d_user = relationship("User", back_populates="d_tasks")
    project = relationship("Project", back_populates="tasks")