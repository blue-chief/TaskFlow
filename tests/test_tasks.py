from app.services.email import outbox


def register_and_login(client, username):
    email = f"{username}@x.com"

    response = client.post(
        "/users/register",
        json={
            "username": username,
            "email": email,
            "password": "correct-horse-battery"
        }
    )

    assert response.status_code == 201

    sent = next(m for m in outbox if m.to == email)

    raw_token = sent.text.split("token=")[1].split("\n")[0].strip()

    response = client.post(
        "/auth/verify-email",
        json={"token": raw_token}
    )

    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": "correct-horse-battery"
        }
    )

    assert response.status_code == 200

    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def test_create_task(client):
    headers = register_and_login(client, "task_user1")

    response = client.post(
        "/tasks",
        json={"title": "Test task"},
        headers=headers
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Test task"


def test_get_task(client):
    headers = register_and_login(client, "task_user2")

    created = client.post(
        "/tasks",
        json={"title": "Findable"},
        headers=headers
    ).json()

    response = client.get(
        f"/tasks/{created['id']}",
        headers=headers
    )

    assert response.status_code == 200


def test_get_missing_task(client):
    headers = register_and_login(client, "task_user3")

    response = client.get(
        "/tasks/99999",
        headers=headers
    )

    assert response.status_code == 404