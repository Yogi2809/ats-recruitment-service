from fastapi.testclient import TestClient


def make_client(tmp_path):
    from backend.app.main import create_app

    return TestClient(create_app(f"sqlite:///{tmp_path / 'users.db'}", "test-secret"))


def register(client, email):
    result = client.post("/api/auth/register", json={"email": email, "password": "long-demo-password"})
    assert result.status_code == 201


def test_workspace_and_comparison_require_login(tmp_path):
    with make_client(tmp_path) as client:
        assert client.get("/api/workspace").status_code == 401
        register(client, "one@example.test")
        workspace = client.get("/api/workspace")
        assert workspace.status_code == 200
        assert len(workspace.json()["jds"]) >= 2
        assert len(workspace.json()["candidates"]) >= 6
        matches = client.get("/api/compare")
        assert matches.status_code == 200
        assert matches.json()["results"][0]["score"] >= matches.json()["results"][1]["score"]


def test_pasted_candidate_is_isolated_by_account(tmp_path):
    with make_client(tmp_path) as alice:
        register(alice, "alice@example.test")
        added = alice.post("/api/candidates/paste", json={"name": "Extra Candidate", "text": "Python and SQL"})
        assert added.status_code == 201
        assert len(alice.get("/api/workspace").json()["candidates"]) == 7
    with make_client(tmp_path) as bob:
        register(bob, "bob@example.test")
        assert len(bob.get("/api/workspace").json()["candidates"]) == 6


def test_workspace_survives_app_restart(tmp_path):
    with make_client(tmp_path) as first:
        register(first, "persist@example.test")
        added = first.post("/api/candidates/paste", json={"name": "Extra Candidate", "text": "Python and SQL"})
        assert added.status_code == 201
    with make_client(tmp_path) as second:
        login = second.post("/api/auth/login", json={"email": "persist@example.test", "password": "long-demo-password"})
        assert login.status_code == 200
        assert any(c["name"] == "Extra Candidate" for c in second.get("/api/workspace").json()["candidates"])


def test_pasted_jd_separates_required_and_preferred_skills_on_one_line(tmp_path):
    with make_client(tmp_path) as client:
        register(client, "jd-sections@example.test")
        added = client.post("/api/jds/paste", json={
            "title": "Data Analyst",
            "text": "Required skills: Python, SQL, and data pipelines. Preferred: AWS.",
        })
        assert added.status_code == 201
        assert added.json()["required"] == ["Python", "SQL", "Data Pipelines"]
        assert added.json()["preferred"] == ["AWS"]


def test_chat_and_draft_work_without_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with make_client(tmp_path) as client:
        register(client, "demo@example.test")
        reply = client.post("/api/chat", json={"question": "Why is Maya ranked first?"})
        assert reply.status_code == 200
        assert reply.json()["citations"]
        draft = client.post("/api/drafts/generate", json={"candidate_id": "maya", "kind": "invitation", "date": "10 Nov 2026", "time": "14:00 IST", "link": "https://example.test/meet"})
        assert draft.status_code == 200
        assert "Interview" in draft.json()["text"]
