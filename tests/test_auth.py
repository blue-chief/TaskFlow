# tests/test_auth.py
from app.services.email import outbox

def register_and_verify(client, username):
    """Registers, then verifies via the ACTUAL emailed token — not a shortcut
    around it — the same way a real click on the link would."""
    response = client.post("/users/register", json={"username": username, "email": f"{username}@x.com", "password": "correct-horse-battery"})
    print("Registration:", response.status_code)
    print("Details:", response.json())
    sent = next(m for m in outbox if m.to == f"{username}@x.com")
    raw_token = sent.text.split("token=")[1].split("\n")[0].strip()
    client.post("/auth/verify-email", json={"token": raw_token})

def test_login_blocked_before_verification(client):
    client.post("/users/register", json={"username": "aaa", "email": "aaa@x.com", "password": "correct-horse-battery"})
    response = client.post("/auth/login", json={"username": "aaa", "password": "correct-horse-battery"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "email_not_verified"

def test_register_verify_and_login(client):
    register_and_verify(client, "aaa")
    response = client.post("/auth/login", json={"username": "aaa", "password": "correct-horse-battery"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(client):
    register_and_verify(client, "bbb")
    response = client.post("/auth/login", json={"username": "bbb", "password": "wrong-password-entirely"})
    assert response.status_code == 401

def test_invalid_token(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401

def test_reset_password_invalidates_old_session(client):
    register_and_verify(client, "ccc")
    old_token = client.post("/auth/login", json={"username": "ccc", "password": "correct-horse-battery"}).json()["access_token"]

    client.post("/auth/forgot-password", json={"email": "ccc@x.com"})
    sent = [m for m in outbox if m.to == "ccc@x.com" and "Reset" in m.subject][-1]
    raw_reset_token = sent.text.split("token=")[1].split("\n")[0].strip()
    client.post("/auth/reset-password", json={"token": raw_reset_token, "new_password": "a-brand-new-password-here"})

    # the OLD token must now be rejected — token_version bumped on reset
    assert client.get("/users/me", headers={"Authorization": f"Bearer {old_token}"}).status_code == 401

def test_user_cannot_delete_others_project(client):
    # Register user A
    response = client.post(
        "/users/register",
        json={
            "username": "user_a",
            "email": "a@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201

    sent = next(m for m in outbox if m.to == "a@example.com")
    raw_token = sent.text.split("token=")[1].split("\n")[0].strip()
    client.post("/auth/verify-email", json={"token": raw_token})

    # Login user A
    response = client.post(
        "/auth/login",
        json={
            "username": "user_a",
            "password": "password123",
        },
    )

    print("Registration:", response.status_code)
    print("Details:", response.json())
    assert response.status_code == 200

    token_a = response.json()["access_token"]

    # Create project as A
    response = client.post(
        "/projects",
        json={"name": "User A Project"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 201

    project_id = response.json()["id"]

    # Register user B
    response = client.post(
        "/users/register",
        json={
            "username": "user_b",
            "email": "b@example.com",
            "password": "password1234",
        },
    )
    assert response.status_code == 201

    sent = next(m for m in outbox if m.to == "b@example.com")
    raw_token = sent.text.split("token=")[1].split("\n")[0].strip()
    client.post("/auth/verify-email", json={"token": raw_token})

    # Login user B
    response = client.post(
        "/auth/login",
        json={
            "username": "user_b",
            "password": "password1234",
        },
    )
    assert response.status_code == 200

    token_b = response.json()["access_token"]
    

    # B tries to delete A's project
    response = client.delete(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 403