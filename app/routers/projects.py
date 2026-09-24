from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends, Query

from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectOut, ProjectPatch, ProjectUpdate
from app.models.project import Project as ProjectModel

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=list[ProjectOut], status_code=status.HTTP_200_OK)
def list_project(
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return db.query(ProjectModel).offset(skip).limit(limit).all()

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
):
    new_project = ProjectModel(name=project.name)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/{project_id}", response_model=ProjectOut, status_code=status.HTTP_200_OK)
def get_project(project_id: int, db:Annotated[Session, Depends(get_db)]):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectOut, status_code=status.HTTP_200_OK)
def update_project(project_id: int, project_update: ProjectUpdate, db: Annotated[Session, Depends(get_db)]):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_update.model_dump()

    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)

    return project

@router.patch("/{project_id}", response_model=ProjectOut, status_code=status.HTTP_200_OK)
def patch_project(project_id:int, project_patch: ProjectPatch, db: Annotated[Session, Depends(get_db)]):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_patch.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)

    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Annotated[Session, Depends(get_db)]):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return None