from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
    task = relationship("Task")
