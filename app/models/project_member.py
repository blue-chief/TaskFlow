from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint
from app.database import Base
from sqlalchemy.orm import relationship

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member") # owner / member

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "user_id",
            name="uq_project_member"
        ),
    )