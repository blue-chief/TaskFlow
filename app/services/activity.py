from app.models.activity import Activity

def log_activity(db, task_id, user_id, description):
    activity = Activity(
        task_id=task_id,
        user_id=user_id,
        description=description,
    )
    db.add(activity)