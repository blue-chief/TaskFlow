from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends, Query, Path
from sqlalchemy.orm import Session
from app.models.user import User as UserModel
from app.models.project import Project as ProjectModel
from app.models.project_member import ProjectMember as ProjectMemberModel
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberOut
from app.core.security import get_current_user, get_db

router = APIRouter(prefix="/projects", tags=["project_members"])

@router.post("/{project_id}/members", response_model=ProjectMemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    project_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    member: ProjectMemberCreate,
    db: Annotated[Session, Depends(get_db)],
):
    project = db.query(ProjectModel).filter(
    ProjectModel.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the project owner can add members"
        )

    is_member = db.query(ProjectMemberModel).filter(
        ProjectMemberModel.project_id == project_id,
        ProjectMemberModel.user_id == member.user_id,
    ).first()

    user = db.query(UserModel).filter(UserModel.id == member.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not is_member:
        new_member = ProjectMemberModel(project_id=project_id, user_id=member.user_id)
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        return new_member
    else:
        raise HTTPException(status_code=409, detail="User is already a Project Member")


@router.get("/{project_id}/members", response_model=list[ProjectMemberOut], status_code=status.HTTP_200_OK)
def get_members(
    project_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    project_exists = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project_exists:
        raise HTTPException(status_code=404, detail="Project does not exists")
    
    is_member = db.query(ProjectMemberModel).filter(
        ProjectMemberModel.project_id == project_id,
        ProjectMemberModel.user_id == current_user.id,
        ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Must be a member to access Project members")
    
    return db.query(ProjectMemberModel).filter(ProjectMemberModel.project_id == project_id).offset(skip).limit(limit).all()