from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from dataclasses import asdict


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
        assert workspace.json()["jds"] == []
        assert workspace.json()["candidates"] == []
        assert workspace.json()["selected_jd_id"] == ""
        matches = client.get("/api/compare")
        assert matches.status_code == 200
        assert matches.json() == {"jd": None, "results": []}


def test_empty_workspace_guides_chat_and_requires_a_jd_for_drafts(tmp_path):
    with make_client(tmp_path) as client:
        register(client, "empty@example.test")
        reply = client.post("/api/chat", json={"question": "Who is the top match?"})
        assert reply.status_code == 200
        assert "job description" in reply.json()["text"].lower()
        assert reply.json()["citations"] == []
        candidate = client.post("/api/candidates/paste", json={"name": "Test Candidate", "text": "Python and SQL"})
        assert candidate.status_code == 201
        assert client.get("/api/compare").json()["results"] == []
        draft = client.post("/api/drafts/generate", json={"candidate_id": candidate.json()["id"], "kind": "invitation"})
        assert draft.status_code == 409
        assert "job description" in draft.json()["detail"].lower()


def test_uploaded_material_completes_comparison_after_empty_start(tmp_path):
    with make_client(tmp_path) as client:
        register(client, "flow@example.test")
        candidate = client.post("/api/candidates/paste", json={"name": "Test Candidate", "text": "Built Python services with SQL."})
        jd = client.post("/api/jds/paste", json={"title": "Data role", "text": "Required: Python, SQL, Airflow."})
        assert jd.status_code == 201
        comparison = client.get("/api/compare")
        assert comparison.status_code == 200
        assert comparison.json()["jd"]["title"] == "Data role"
        assert comparison.json()["results"][0]["candidate_id"] == candidate.json()["id"]
        assert comparison.json()["results"][0]["missing_required"] == ["Airflow"]


def test_pasted_candidate_is_isolated_by_account(tmp_path):
    with make_client(tmp_path) as alice:
        register(alice, "alice@example.test")
        added = alice.post("/api/candidates/paste", json={"name": "Extra Candidate", "text": "Python and SQL"})
        assert added.status_code == 201
        assert len(alice.get("/api/workspace").json()["candidates"]) == 1
    with make_client(tmp_path) as bob:
        register(bob, "bob@example.test")
        assert bob.get("/api/workspace").json()["candidates"] == []
        assert bob.get(f"/api/candidates/{added.json()['id']}/analysis").status_code == 404


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


def test_first_workspace_requests_can_arrive_together(tmp_path, monkeypatch):
    from backend.app import main

    barrier = Barrier(2)
    original = main.Workspace

    def concurrent_workspace(*args, **kwargs):
        barrier.wait(timeout=5)
        return original(*args, **kwargs)

    monkeypatch.setattr(main, "Workspace", concurrent_workspace)
    with make_client(tmp_path) as client:
        register(client, "first-login@example.test")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(client.get, ["/api/workspace", "/api/compare"]))
        assert [response.status_code for response in results] == [200, 200]


def test_chat_and_draft_work_without_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with make_client(tmp_path) as client:
        register(client, "demo@example.test")
        jd = client.post("/api/jds/paste", json={"title": "Data Engineer", "text": "Required: Python, SQL, Airflow."})
        assert jd.status_code == 201
        candidate = client.post("/api/candidates/paste", json={"name": "Maya Test", "text": "Built Python and SQL pipelines using Airflow."})
        assert candidate.status_code == 201
        reply = client.post("/api/chat", json={"question": "Why is Maya ranked first?"})
        assert reply.status_code == 200
        assert reply.json()["citations"]
        draft = client.post("/api/drafts/generate", json={"candidate_id": candidate.json()["id"], "kind": "invitation", "date": "10 Nov 2026", "time": "14:00 IST", "link": "https://example.test/meet"})
        assert draft.status_code == 200
        assert "Interview" in draft.json()["text"]


def test_old_account_can_remove_bundled_samples_without_losing_own_documents(tmp_path):
    from backend.app.auth import WorkspaceRecord
    from backend.app.main import create_app
    from backend.app.sample_data import sample_workspace

    app = create_app(f"sqlite:///{tmp_path / 'legacy.db'}", "legacy-test-secret")
    with TestClient(app) as client:
        assert client.delete("/api/workspace/sample-data").status_code == 401
        registration = client.post("/api/auth/register", json={"email": "legacy@example.test", "password": "long-demo-password"})
        user_id = registration.json()["id"]
        with app.state.auth.session_factory() as session:
            session.add(WorkspaceRecord(user_id=user_id, payload=asdict(sample_workspace())))
            session.commit()
        jd = client.post("/api/jds/paste", json={"title": "My Role", "text": "Required: SQL."})
        candidate = client.post("/api/candidates/paste", json={"name": "My Candidate", "text": "Built SQL reports."})
        assert jd.status_code == candidate.status_code == 201
        sample_draft = client.post("/api/drafts/generate", json={"candidate_id": "maya", "kind": "invitation"})
        assert sample_draft.status_code == 200

        cleared = client.delete("/api/workspace/sample-data")
        assert cleared.status_code == 200
        saved = client.get("/api/workspace").json()
        assert [item["id"] for item in saved["jds"]] == [jd.json()["id"]]
        assert [item["id"] for item in saved["candidates"]] == [candidate.json()["id"]]
        assert saved["selected_jd_id"] == jd.json()["id"]
        assert saved["recruitment"] == []
        assert saved["drafts"] == []


def test_recruitment_stage_is_recorded_per_candidate_and_grounded_in_chat(tmp_path):
    with make_client(tmp_path) as alice:
        register(alice, "stage-alice@example.test")
        alice.post("/api/jds/paste", json={"title": "Engineer", "text": "Required: Python."})
        candidate = alice.post("/api/candidates/paste", json={"name": "Stage Candidate", "text": "Built Python services."}).json()
        before = alice.post("/api/chat", json={"question": "What stage is Stage Candidate at?"})
        assert before.status_code == 200
        assert "not recorded" in before.json()["text"].lower()
        assert alice.patch(f"/api/candidates/{candidate['id']}/recruitment", json={"stage": "  "}).status_code == 422
        saved = alice.patch(f"/api/candidates/{candidate['id']}/recruitment", json={"stage": "Recruiter screen", "assessment": "Data exercise pending"})
        assert saved.status_code == 200
        assert saved.json()["stage"] == "Recruiter screen"
        answer = alice.post("/api/chat", json={"question": "What assessment is Stage Candidate assigned?"})
        assert answer.status_code == 200
        assert "Data exercise pending" in answer.json()["text"]
        assert answer.json()["citations"][0]["source"] == "Recruitment record"
        assert alice.get("/api/workspace").json()["recruitment"][0]["candidate_id"] == candidate["id"]
        updated = alice.patch(f"/api/candidates/{candidate['id']}/recruitment", json={"stage": "Technical interview", "assessment": "Completed"})
        assert updated.status_code == 200
        assert len(alice.get("/api/workspace").json()["recruitment"]) == 1
        assert alice.delete(f"/api/candidates/{candidate['id']}").status_code == 200
        assert alice.get("/api/workspace").json()["recruitment"] == []
    with make_client(tmp_path) as bob:
        register(bob, "stage-bob@example.test")
        assert bob.patch(f"/api/candidates/{candidate['id']}/recruitment", json={"stage": "Offer"}).status_code == 404


def test_duplicate_email_explains_login_instead_of_creating_account(tmp_path):
    with make_client(tmp_path) as client:
        register(client, "already@example.test")
        response = client.post("/api/auth/register", json={"email": " ALREADY@example.test ", "password": "another-long-password"})
        assert response.status_code == 409
        assert response.json()["detail"] == "This email is already registered. Log in instead."


def test_qa_job_extracts_testing_skills_for_comparison(tmp_path):
    with make_client(tmp_path) as client:
        register(client, "qa-role@example.test")
        response = client.post("/api/jds/paste", json={"title": "QA Engineer", "text": "Required: manual testing, test cases, Selenium, API testing, and Jira."})
        assert response.status_code == 201
        assert {"Manual Testing", "Test Cases", "Selenium", "API Testing", "Jira"}.issubset(set(response.json()["required"]))
