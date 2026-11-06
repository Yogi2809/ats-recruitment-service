from fastapi.testclient import TestClient


def client_for(tmp_path):
    from backend.app.main import create_app

    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'users.db'}",
        secret_key="test-secret-for-auth",
    )
    return TestClient(app)


def test_registration_login_logout_and_protection(tmp_path):
    with client_for(tmp_path) as client:
        assert client.get("/api/auth/me").status_code == 401
        created = client.post(
            "/api/auth/register",
            json={"email": "Recruiter@Example.test", "password": "long-demo-password"},
        )
        assert created.status_code == 201
        assert created.json()["email"] == "recruiter@example.test"
        assert "password" not in created.json()
        assert client.get("/api/auth/me").json()["email"] == "recruiter@example.test"
        assert client.post("/api/auth/logout").status_code == 200
        assert client.get("/api/auth/me").status_code == 401
        assert client.post(
            "/api/auth/login",
            json={"email": "recruiter@example.test", "password": "long-demo-password"},
        ).status_code == 200


def test_wrong_credentials_have_same_error_and_duplicate_is_rejected(tmp_path):
    with client_for(tmp_path) as client:
        client.post(
            "/api/auth/register",
            json={"email": "a@example.test", "password": "long-demo-password"},
        )
        client.post("/api/auth/logout")
        wrong_email = client.post(
            "/api/auth/login",
            json={"email": "missing@example.test", "password": "long-demo-password"},
        )
        wrong_password = client.post(
            "/api/auth/login",
            json={"email": "a@example.test", "password": "wrong-password"},
        )
        assert wrong_email.status_code == wrong_password.status_code == 401
        assert wrong_email.json() == wrong_password.json()
        assert client.post(
            "/api/auth/register",
            json={"email": "A@example.test", "password": "other-long-password"},
        ).status_code == 409


def test_account_survives_new_app_instance(tmp_path):
    with client_for(tmp_path) as client:
        client.post(
            "/api/auth/register",
            json={"email": "saved@example.test", "password": "long-demo-password"},
        )
    with client_for(tmp_path) as another_client:
        result = another_client.post(
            "/api/auth/login",
            json={"email": "saved@example.test", "password": "long-demo-password"},
        )
        assert result.status_code == 200
