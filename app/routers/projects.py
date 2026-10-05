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
from app.schemas.task import TaskOut, TaskCreate
from app.core.security import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=list[ProjectOut], status_code=status.HTTP_200_OK)
def list_project(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    projects = db.query(ProjectModel).filter(ProjectModel.owner_id == current_user.id)
    if not projects:
        raise HTTPException(status_code=404, detail="No Project Found")
    
    projects = projects.offset(skip).limit(limit).all()

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    current_user: Annotated[UserModel, Depends(get_current_user)],
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
    db:Annotated[Session, Depends(get_db)],
):
    projects = db.query(ProjectModel).filter(ProjectModel.owner_id == current_user.id)
    if not projects:
        raise HTTPException(status_code=404, detail="No Project Found")
    
    project = projects.filter(ProjectModel.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectOut, status_code=status.HTTP_200_OK)
def update_project(
    project_id: int, project_update: ProjectUpdate, 
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    projects = db.query(ProjectModel).filter(ProjectModel.owner_id == current_user.id)
    if not projects:
        raise HTTPException(status_code=404, detail="No Project Found")
        
    project = projects.filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = db.query(ProjectModel).filter(ProjectModel.owner_id == current_user.id).first()
    if not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden, Not your project")
    
    update_data = project_update.model_dump()

    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)

    return project

@router.patch("/{project_id}", response_model=ProjectOut, status_code=status.HTTP_200_OK)
def patch_project(
    project_id:int, project_patch: ProjectPatch, 
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = db.query(ProjectModel).filter(ProjectModel.owner_id == current_user.id).first()
    if not is_owner:
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
    db: Annotated[Session, Depends(get_db)]):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden, Not your project")
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
    project_exists = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project_exists:
        raise HTTPException(status_code=404, detail="Project does not exists")

    is_owner = db.query(ProjectModel).filter(ProjectModel.owner_id == current_user.id).first()
    if not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden, Not your project")

    new_task = TaskModel(title=task.title, description=task.description, project_id=project_id, status=task.status, priority=task.priority)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

@router.patch("/{project_id}/tasks/{task_id}", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def patch_project_task(
    project_id: Annotated[int, Path()],
    task_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    project_exists = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project_exists:
        raise HTTPException(status_code=404, detail="Project does not exists")

    is_owner = db.query(ProjectModel).filter(ProjectModel.owner_id == current_user.id).first()
    if not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden, Not your project")

    task = db.query(TaskModel).join(TaskModel.project, isouter=True).filter(
                or_(
                    TaskModel.assigned_to_id == current_user.id,
                    ProjectModel.owner_id == current_user.id
                )
            )
    task_exists = task.filter(TaskModel.id == task_id).first()

    if not task_exists:
        raise HTTPException(status_code=404, detail="Task not found")

    task_exists.project_id = project_id
    db.commit()
    db.refresh(task_exists)

    return task_exists