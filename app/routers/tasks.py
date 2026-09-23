from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Depends, status

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task import Task as TaskModel
from app.schemas.task import TaskCreate, TaskOut, TaskPatch, TaskUpdate, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("", response_model=list[TaskOut], status_code=status.HTTP_200_OK)
def list_task(
    db: Annotated[Session, Depends(get_db)],
    # status: Annotated[TaskStatus | None, Query()] = None,
    # priority: Annotated[str | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    # if status is not None:
    #     results = [t for t in results if t.get("status") == status]
    # if priority is not None:
    #     results = [t for t in results if t.get("priority") == priority]
    return db.query(TaskModel).offset(skip).limit(limit).all()

@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Annotated[Session, Depends(get_db)]):
    new_task = TaskModel(title=task.title, description=task.description)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.get("/{task_id}", response_model=TaskOut, status_code=status.HTTP_200_OK)
def get_task(task_id : int, db: Annotated[Session, Depends(get_db)]):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskOut, status_code=status.HTTP_200_OK)
def update_task(task_id: int, task_update: TaskUpdate, db: Annotated[Session, Depends(get_db)]):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump()

    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)

    return task
    

@router.patch("/{task_id}", response_model=TaskOut, status_code=status.HTTP_200_OK)
def patch_task(task_id: int, task_patch: TaskPatch, db: Annotated[Session, Depends(get_db)]):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_patch.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)

    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Annotated[Session, Depends(get_db)]):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return None