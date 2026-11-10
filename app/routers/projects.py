from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends, Query, Path

from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectOut, ProjectPatch, ProjectUpdate, ProjectOutFull
from app.models.project import Project as ProjectModel
from app.models.project_member import ProjectMember as ProjectMemberModel
from app.models.user import User as UserModel
from app.models.task import Task as TaskModel
from app.schemas.task import TaskOut, TaskCreate, TaskPatch
from app.core.security import get_current_user, get_verified_user
from app.core.permissions import require_project_role

router = APIRouter(prefix="/projects", tags=["projects"])

def get_project_membership(db: Session, project_id: int, user_id: int):
    return db.query(ProjectMemberModel).filter(
        ProjectMemberModel.project_id == project_id,
        ProjectMemberModel.user_id == user_id,
    ).first()

@router.get("", response_model=list[ProjectOut], status_code=status.HTTP_200_OK)
def list_project(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    member_project_ids = db.query(ProjectMemberModel.project_id).filter(
        ProjectMemberModel.user_id == current_user.id
    )
    projects = db.query(ProjectModel).filter(
        or_(
            ProjectModel.owner_id == current_user.id,
            ProjectModel.id.in_(member_project_ids)
        )
    ).distinct().offset(skip).limit(limit).all()

    return projects

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    current_user: Annotated[UserModel, Depends(get_verified_user)],
    project: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
):
    new_project = ProjectModel(name=project.name, owner_id=current_user.id)
    db.add(new_project)
    db.flush()
    
    new_owner = ProjectMemberModel(project_id=new_project.id, user_id=current_user.id, role="owner")
    db.add(new_owner)
    db.commit()

    db.refresh(new_project)
    return new_project

@router.get("/{project_id}", response_model=ProjectOutFull, status_code=status.HTTP_200_OK)
def get_project(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    project_id: int, 
    db: Annotated[Session, Depends(get_db)],
):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_member = (project.owner_id == current_user.id) or bool(get_project_membership(db, project_id, current_user.id))
    if not is_member:
        raise HTTPException(status_code=403, detail="Forbidden, Not a member of this project")

    return project

@router.put("/{project_id}", response_model=ProjectOut, status_code=status.HTTP_200_OK)
def update_project(
    project_id: int,
    project_update: ProjectUpdate, 
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden, Not your project")
    
    update_data = project_update.model_dump()
    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return project

@router.patch("/{project_id}", response_model=ProjectOut, status_code=status.HTTP_200_OK)
def patch_project(
    project_id: int,
    project_patch: ProjectPatch, 
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden, Not your project")
    
    update_data = project_patch.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int, 
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_role(db, project_id, current_user, allowed_roles={"owner"})
    db.delete(project)
    db.commit()
    return None

@router.post("/{project_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_project_task(
    project_id: Annotated[int, Path()],
    task: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project does not exist")

    is_member = (project.owner_id == current_user.id) or bool(get_project_membership(db, project_id, current_user.id))
    if not is_member:
        raise HTTPException(status_code=403, detail="Forbidden, Not a member of this project")

    new_task = TaskModel(
        title=task.title,
        description=task.description,
        project_id=project_id,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        assigned_to_id=current_user.id,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.patch("/{project_id}/tasks/{task_id}", response_model=TaskOut, status_code=status.HTTP_200_OK)
def patch_project_task(
    project_id: Annotated[int, Path()],
    task_id: Annotated[int, Path()],
    task_patch: TaskPatch,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project does not exist")

    is_member = (project.owner_id == current_user.id) or bool(get_project_membership(db, project_id, current_user.id))
    if not is_member:
        raise HTTPException(status_code=403, detail="Forbidden, Not a member of this project")

    task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_patch.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task
