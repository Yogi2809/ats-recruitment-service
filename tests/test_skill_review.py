from dataclasses import asdict

from fastapi.testclient import TestClient

from backend.app.auth import WorkspaceRecord
from backend.app.documents import extract_paste
from backend.app.main import create_app
from backend.app.models import JobDescription, Workspace


def client_for(tmp_path):
    return TestClient(create_app(f"sqlite:///{tmp_path / 'review.db'}", "review-secret"))


def register(client, email="review@example.test"):
    response = client.post("/api/auth/register", json={"email": email, "password": "long-demo-password"})
    assert response.status_code == 201
    return response.json()["id"]


def test_new_jd_needs_review_before_comparison(tmp_path):
    with client_for(tmp_path) as client:
        register(client)
        jd = client.post("/api/jds/paste", json={"title": "QA Engineer", "text": "Requirements:\nSelenium and Manual Testing."})
        assert jd.status_code == 201
        assert jd.json()["needs_review"] is True
        client.post("/api/candidates/paste", json={"name": "Example", "text": "Used Selenium for tests."})
        assert client.get("/api/compare").json()["results"] == []
        assert client.get("/api/workspace").json()["jds"][0]["needs_review"] is True


def test_preview_is_read_only_and_review_enables_scoring(tmp_path):
    with client_for(tmp_path) as client:
        register(client)
        jd = client.post("/api/jds/paste", json={"title": "QA Engineer", "text": "Requirements:\nSelenium and Manual Testing."}).json()
        client.post("/api/candidates/paste", json={"name": "Example", "text": "Used Selenium for tests."})
        before = client.get("/api/workspace").json()
        preview = client.post(f"/api/jds/{jd['id']}/skills/preview", json={})
        assert preview.status_code == 200
        assert client.get("/api/workspace").json() == before
        choices = [item for item in preview.json()["suggestions"] if item["label"] in {"Selenium", "Manual Testing"}]
        saved = client.put(f"/api/jds/{jd['id']}/skills", json={"selected_role": preview.json()["selected_role"], "requirements": choices})
        assert saved.status_code == 200
        assert saved.json()["needs_review"] is False
        assert {"Selenium", "Manual Testing"}.issubset(set(saved.json()["required"]))
        result = client.get("/api/compare").json()["results"][0]
        assert result["matched_required"] == ["Selenium"]
        assert "Manual Testing" in result["missing_required"]


def test_legacy_jd_requires_review_without_erasing_old_skills(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'legacy.db'}", "legacy-secret")
    with TestClient(app) as client:
        user_id = register(client, "legacy-review@example.test")
        assert client.get("/api/workspace").status_code == 200
        old = JobDescription("old", "QA Engineer", ["React", "AWS"], [], extract_paste("QA Engineer\nRequirements:\nSelenium."))
        with app.state.auth.session_factory() as session:
            record = session.get(WorkspaceRecord, user_id)
            record.payload = asdict(Workspace([old], [], "old"))
            session.commit()
        before = client.get("/api/workspace").json()["jds"][0]
        assert before["needs_review"] is True
        assert before["required"] == ["React", "AWS"]
        preview = client.post("/api/jds/old/skills/preview", json={}).json()
        assert any(item["label"] == "Selenium" for item in preview["suggestions"])
        assert client.get("/api/workspace").json()["jds"][0]["required"] == ["React", "AWS"]


def test_skill_preview_and_save_are_private_and_forged_sources_rejected(tmp_path):
    with client_for(tmp_path) as alice:
        register(alice, "alice-review@example.test")
        jd = alice.post("/api/jds/paste", json={"title": "QA", "text": "Requirements:\nSelenium."}).json()
        preview = alice.post(f"/api/jds/{jd['id']}/skills/preview", json={}).json()
        fake = {**preview["suggestions"][0], "source_id": "some-other-document"}
        assert alice.put(f"/api/jds/{jd['id']}/skills", json={"selected_role": None, "requirements": [fake]}).status_code == 422
    with client_for(tmp_path) as bob:
        register(bob, "bob-review@example.test")
        assert bob.post(f"/api/jds/{jd['id']}/skills/preview", json={}).status_code == 404
        assert bob.put(f"/api/jds/{jd['id']}/skills", json={"selected_role": None, "requirements": []}).status_code == 404


def test_alternative_group_counts_once_and_matches_any_option(tmp_path):
    with client_for(tmp_path) as client:
        register(client)
        jd = client.post("/api/jds/paste", json={"title": "Backend Developer", "text": "Required Skills:\nAWS, GCP, or Azure."}).json()
        candidate = client.post("/api/candidates/paste", json={"name": "Cloud Engineer", "text": "Deployed services to GCP."}).json()
        preview = client.post(f"/api/jds/{jd['id']}/skills/preview", json={}).json()
        group = next(item for item in preview["suggestions"] if item["label"] == "AWS or GCP or Azure")
        saved = client.put(f"/api/jds/{jd['id']}/skills", json={"selected_role": preview["selected_role"], "requirements": [group]})
        assert saved.status_code == 200
        result = client.get("/api/compare").json()["results"][0]
        assert result["candidate_id"] == candidate["id"]
        assert result["required_percent"] == 100
        assert result["matched_required"] == ["AWS or GCP or Azure"]
