from app.services.email import outbox
from tests.test_tasks import register_and_login

def test_project_visibility_and_member_flow(client):
    owner_headers = register_and_login(client, "project_owner")
    member_headers = register_and_login(client, "project_member")

    # 1. Owner creates a project
    res = client.post("/projects", json={"name": "Alpha Project"}, headers=owner_headers)
    assert res.status_code == 201
    project_id = res.json()["id"]

    # 2. Member cannot see it yet in their project list
    res = client.get("/projects", headers=member_headers)
    assert res.status_code == 200
    assert len(res.json()) == 0

    # 3. Owner adds member by username
    res = client.post(
        f"/projects/{project_id}/members",
        json={"username": "project_member"},
        headers=owner_headers,
    )
    assert res.status_code == 201
    assert res.json()["username"] == "project_member"

    # 4. Now member sees the project in their list
    res = client.get("/projects", headers=member_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == project_id

    # 5. Member creates a task in the project
    res = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Member Created Task", "description": "A task created by invited member"},
        headers=member_headers,
    )
    assert res.status_code == 201
    task_id = res.json()["id"]
    assert res.json()["project_id"] == project_id
    assert res.json()["status"] == "todo"
    assert res.json()["priority"] == "low"

    # 6. Fetch tasks by project_id
    res = client.get(f"/tasks?project_id={project_id}", headers=owner_headers)
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_id
    assert tasks[0]["status"] == "todo"
    assert tasks[0]["assigned_to"]["username"] == "project_member"

    # 7. Post comment using 'content' (frontend payload format)
    res = client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "Looks good, working on it."},
        headers=owner_headers,
    )
    assert res.status_code == 201
    assert res.json()["content"] == "Looks good, working on it."
    assert res.json()["body"] == "Looks good, working on it."

    # 8. Get comments
    res = client.get(f"/tasks/{task_id}/comments", headers=member_headers)
    assert res.status_code == 200
    comments = res.json()
    assert len(comments) == 1
    assert comments[0]["content"] == "Looks good, working on it."

    # 9. Get task activity
    res = client.get(f"/tasks/{task_id}/activity", headers=member_headers)
    assert res.status_code == 200
    activities = res.json()
    assert len(activities) >= 1
    assert any("comment" in a["description"].lower() for a in activities)

