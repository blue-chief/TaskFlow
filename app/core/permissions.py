from typing import Annotated
from fastapi import Depends, HTTPException
from app.models.user import User as UserModel
from sqlalchemy.orm import Session
from app.database import get_db

from app.models.project_member import ProjectMember as ProjecctMemberModel

def require_project_role(
    db: Annotated[Session, Depends(get_db)],
    project_id: int,
    user: UserModel, 
    allowed_roles: set[str]
):
    if user.is_admin:
        return

    membership = db.query(ProjecctMemberModel).filter(
        ProjecctMemberModel.project_id == project_id,
        ProjecctMemberModel.user_id == user.id,
    ).first()

    if not membership or membership.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Not authorized for this action")