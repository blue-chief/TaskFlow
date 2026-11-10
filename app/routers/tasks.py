from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Path, Depends, status

from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.task import Task as TaskModel, TaskPriorityEnum, TaskStatusEnum
from app.models.user import User as UserModel
from app.models.project import Project as ProjectModel
from app.models.project_member import ProjectMember as ProjectMemberModel
from app.models.comment import Comment as CommentModel
from app.models.activity import Activity as ActivityModel
from app.services.activity import log_activity
from app.core.security import get_current_user
from app.schemas.task import (
    TaskCreate,
    TaskOut,
    TaskPatch,
    TaskUpdate,
    TaskOutFull,
    TaskPatchPriority,
    TaskPatchStatus,
    TaskPostComment,
    TaskCommentOut,
    ActivityOut,
)
from app.core.permissions import require_project_role

router = APIRouter(prefix="/tasks", tags=["tasks"])

def user_has_task_access(db: Session, task: TaskModel, user: UserModel) -> bool:
    if task.assigned_to_id == user.id:
        return True
    if not task.project_id:
        return True
    project = task.project or db.query(ProjectModel).filter(ProjectModel.id == task.project_id).first()
    if project and project.owner_id == user.id:
        return True
    is_member = db.query(ProjectMemberModel).filter(
        ProjectMemberModel.project_id == task.project_id,
        ProjectMemberModel.user_id == user.id,
    ).first()
    return bool(is_member)

@router.get("", response_model=list[TaskOut], status_code=status.HTTP_200_OK)
def list_task(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    project_id: Annotated[int | None, Query()] = None,
    status: Annotated[TaskStatusEnum | None, Query()] = None,
    priority: Annotated[TaskPriorityEnum | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    search: Annotated[str | None, Query()] = None,
    sort: Annotated[str | None, Query()] = None,
    assigned_to_id: Annotated[int | None, Query()] = None,
):
    SORTABLE_FIELDS = {"due_date": TaskModel.due_date, "priority": TaskModel.priority, "id": TaskModel.id}

    member_project_ids = db.query(ProjectMemberModel.project_id).filter(
        ProjectMemberModel.user_id == current_user.id
    )

    query = db.query(TaskModel).join(TaskModel.project, isouter=True).filter(
        or_(
            TaskModel.assigned_to_id == current_user.id,
            ProjectModel.owner_id == current_user.id,
            TaskModel.project_id.in_(member_project_ids)
        )
    )

    if project_id is not None:
        query = query.filter(TaskModel.project_id == project_id)
    if status is not None:
        query = query.filter(TaskModel.status == status)
    if priority is not None:
        query = query.filter(TaskModel.priority == priority)
    if search:
        query = query.filter(TaskModel.title.ilike(f"%{search}%"))
    if assigned_to_id:
        query = query.filter(TaskModel.assigned_to_id == assigned_to_id)
    if sort and sort in SORTABLE_FIELDS:
        query = query.order_by(SORTABLE_FIELDS[sort])
    elif sort:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    return query.offset(skip).limit(limit).all()

@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskCreate, 
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if task.project_id:
        project = db.query(ProjectModel).filter(ProjectModel.id == task.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        is_member = (project.owner_id == current_user.id) or bool(db.query(ProjectMemberModel).filter(
            ProjectMemberModel.project_id == task.project_id,
            ProjectMemberModel.user_id == current_user.id,
        ).first())
        if not is_member:
            raise HTTPException(status_code=403, detail="Forbidden, Not a member of this project")

    new_task = TaskModel(
        title=task.title, 
        description=task.description, 
        status=task.status, 
        priority=task.priority, 
        due_date=task.due_date,
        project_id=task.project_id,
        assigned_to_id=current_user.id,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.get("/{task_id}", response_model=TaskOutFull, status_code=status.HTTP_200_OK)
def get_task(
    task_id: int, 
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task or not user_has_task_access(db, task, current_user):
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskOut, status_code=status.HTTP_200_OK)
def update_task(
    task_id: int,
    task_update: TaskUpdate, 
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task or not user_has_task_access(db, task, current_user):
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump()
    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task

@router.patch("/{task_id}", response_model=TaskOut, status_code=status.HTTP_200_OK)
def patch_task(
    task_id: int,
    task_patch: TaskPatch, 
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task or not user_has_task_access(db, task, current_user):
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_patch.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int, 
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task or not user_has_task_access(db, task, current_user):
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return None

@router.patch("/{task_id}/assign", response_model=TaskOut, status_code=status.HTTP_200_OK)
def assign_task(
    task_id: int, 
    assignee_id: int, 
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    project_id: int | None = None,
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    target_project_id = project_id or task.project_id
    if target_project_id:
        project = db.query(ProjectModel).filter(ProjectModel.id == target_project_id).first()
        is_allowed = project and ((project.owner_id == current_user.id) or bool(db.query(ProjectMemberModel).filter(
            ProjectMemberModel.project_id == target_project_id,
            ProjectMemberModel.user_id == current_user.id,
        ).first()))
        if not is_allowed:
            raise HTTPException(status_code=403, detail="Forbidden, Not allowed to assign tasks in this project")

    task.assigned_to_id = assignee_id
    log_activity(
        db,
        task_id,
        current_user.id,
        f"assigned task to user {assignee_id}"
    )

    db.commit()
    db.refresh(task)
    return task

@router.patch("/{task_id}/status", response_model=TaskOutFull, status_code=status.HTTP_200_OK)
def patch_task_status(
    task_id: Annotated[int, Path()],
    status: TaskPatchStatus,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task or not user_has_task_access(db, task, current_user):
        raise HTTPException(status_code=403, detail="Forbidden, Must be owner, member or assignee to change status")

    update_data = status.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    log_activity(
        db,
        task_id,
        current_user.id,
        f"changed status to {task.status.value if hasattr(task.status, 'value') else task.status}"
    )

    db.commit()
    db.refresh(task)
    return task

@router.patch("/{task_id}/priority", response_model=TaskOutFull, status_code=status.HTTP_200_OK)
def patch_task_priority(
    task_id: Annotated[int, Path()],
    priority: TaskPatchPriority,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task or not user_has_task_access(db, task, current_user):
        raise HTTPException(status_code=403, detail="Forbidden, Must be owner, member or assignee to change priority")

    update_data = priority.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    log_activity(
        db,
        task_id,
        current_user.id,
        f"changed priority to {task.priority.value if hasattr(task.priority, 'value') else task.priority}"
    )

    db.commit()
    db.refresh(task)
    return task

@router.post("/{task_id}/comments", response_model=TaskCommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    task_id: Annotated[int, Path()],
    comment: TaskPostComment,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task or not user_has_task_access(db, task, current_user):
        raise HTTPException(status_code=403, detail="Forbidden, Must be associated to task to make comment")

    new_comment = CommentModel(
        task_id=task_id,
        author_id=current_user.id,
        body=comment.body,
    )

    log_activity(
        db,
        task_id,
        current_user.id,
        f"added comment: {comment.body[:30]}"
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

@router.get("/{task_id}/comments", response_model=list[TaskCommentOut], status_code=status.HTTP_200_OK)
def get_task_comments(
    task_id: int, 
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task or not user_has_task_access(db, task, current_user):
        raise HTTPException(status_code=403, detail="Forbidden, Must be associated to task to view comments")

    comments = db.query(CommentModel).filter(CommentModel.task_id == task_id).order_by(CommentModel.created_at.asc()).all()
    return comments

@router.get("/{task_id}/activity", response_model=list[ActivityOut], status_code=status.HTTP_200_OK)
def get_task_activity(
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task or not user_has_task_access(db, task, current_user):
        raise HTTPException(status_code=403, detail="Forbidden, Must be associated to task to view activity")

    activities = db.query(ActivityModel).filter(ActivityModel.task_id == task_id).order_by(ActivityModel.created_at.desc()).all()
    return activities
