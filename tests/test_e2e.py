from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

from docx import Document
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas


def app_for(tmp_path):
    from backend.app.main import create_app

    return create_app(f"sqlite:///{tmp_path / 'workflow.db'}", "workflow-test-secret")


def register(client, email):
    response = client.post("/api/auth/register", json={"email": email, "password": "long-demo-password"})
    assert response.status_code == 201


def pdf_with(text):
    output = BytesIO()
    page = canvas.Canvas(output)
    page.drawString(72, 720, text)
    page.showPage()
    page.save()
    return output.getvalue()


def docx_with(text):
    output = BytesIO()
    document = Document()
    document.add_paragraph(text)
    document.save(output)
    return output.getvalue()


def test_recruiter_workflow_and_account_boundaries(tmp_path):
    app = app_for(tmp_path)
    with TestClient(app) as alice, TestClient(app) as bob:
        register(alice, "alice@example.test")
        register(bob, "bob@example.test")
        assert bob.get("/api/workspace").json()["jds"] == []

        jd = alice.post("/api/jds/paste", json={"title": "Data Engineer", "text": "Required: Python, SQL, Airflow. Preferred: AWS."})
        assert jd.status_code == 201
        assert jd.json()["required"] == ["Python", "SQL", "Airflow"]
        cv = alice.post("/api/candidates/upload", files={"file": ("Maya_Test.docx", docx_with("Built Python and SQL pipelines using Airflow and AWS."))})
        assert cv.status_code == 201
        assert cv.json()["name"] == "Maya Test"
        second = alice.post("/api/candidates/paste", json={"name": "Second Test", "text": "Python reporting, no Airflow experience."})
        assert second.status_code == 201

        matches = alice.get("/api/compare")
        assert matches.status_code == 200
        assert [row["candidate_id"] for row in matches.json()["results"]] == [cv.json()["id"], second.json()["id"]]
        assert matches.json()["results"][1]["missing_required"] == ["SQL", "Airflow"]
        analysis = alice.get(f"/api/candidates/{cv.json()['id']}/analysis")
        assert analysis.status_code == 200
        assert "Data Engineer" in analysis.json()["summary"]
        assert any("Airflow" in question for question in analysis.json()["questions"])
        reply = alice.post("/api/chat", json={"question": "Why is Maya a match?", "candidate_id": cv.json()["id"]})
        assert reply.status_code == 200
        assert reply.json()["citations"]

        invitation = alice.post("/api/drafts/generate", json={"candidate_id": cv.json()["id"], "kind": "invitation", "date": "2026-11-10", "time": "14:00", "link": "https://example.test/meet"})
        assert invitation.status_code == 200
        assert "Data Engineer" in invitation.json()["text"]
        draft_id = invitation.json()["id"]
        edited = alice.patch(f"/api/drafts/{draft_id}", json={"text": "Edited interview invitation"})
        assert edited.status_code == 200
        assert edited.json()["text"] == "Edited interview invitation"
        assert alice.get("/api/workspace").json()["drafts"][0]["text"] == "Edited interview invitation"

        assert bob.get("/api/workspace").json()["candidates"] == []
        assert bob.get("/api/compare").json()["results"] == []
        assert bob.get(f"/api/candidates/{cv.json()['id']}/analysis").status_code == 404
        assert bob.post(f"/api/jds/{jd.json()['id']}/select").status_code == 404
        assert bob.patch(f"/api/drafts/{draft_id}", json={"text": "Intrusion"}).status_code == 404
        assert bob.delete(f"/api/drafts/{draft_id}").status_code == 404
        assert alice.get("/api/workspace").json()["drafts"][0]["text"] == "Edited interview invitation"

        assert alice.delete(f"/api/drafts/{draft_id}").status_code == 200
        assert alice.delete(f"/api/candidates/{second.json()['id']}").status_code == 200
        assert len(alice.get("/api/workspace").json()["candidates"]) == 1
        assert alice.post("/api/auth/logout").status_code == 200
        assert alice.get("/api/workspace").status_code == 401
        assert alice.post("/api/auth/login", json={"email": "alice@example.test", "password": "long-demo-password"}).status_code == 200
        assert len(alice.get("/api/workspace").json()["candidates"]) == 1


def test_document_upload_formats_and_invalid_files(tmp_path):
    with TestClient(app_for(tmp_path)) as client:
        register(client, "files@example.test")
        assert client.post("/api/jds/upload", files={"file": ("role.docx", docx_with("Required: Python and SQL."))}).status_code == 201
        pdf = client.post("/api/candidates/upload", files={"file": ("Candidate.pdf", pdf_with("Python SQL"))})
        assert pdf.status_code == 201
        assert pdf.json()["evidence"][0]["location"] == "page 1"
        assert client.post("/api/candidates/upload", files={"file": ("Second.txt", b"Built Python services")}).status_code == 201
        assert client.post("/api/candidates/upload", files={"file": ("bad.png", b"image")}).status_code == 422
        assert client.post("/api/candidates/upload", files={"file": ("empty.txt", b"  ")}).status_code == 422
        assert client.post("/api/candidates/upload", files={"file": ("large.txt", b"x" * (5 * 1024 * 1024 + 1))}).status_code == 422
        assert len(client.get("/api/workspace").json()["candidates"]) == 2


def test_two_recruiters_can_write_at_the_same_time_without_mixing_data(tmp_path):
    app = app_for(tmp_path)
    with TestClient(app) as alice, TestClient(app) as bob:
        register(alice, "concurrent-alice@example.test")
        register(bob, "concurrent-bob@example.test")
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(alice.post, "/api/candidates/paste", json={"name": "Alice Candidate", "text": "Python"})
            second = pool.submit(bob.post, "/api/candidates/paste", json={"name": "Bob Candidate", "text": "SQL"})
            assert first.result().status_code == 201
            assert second.result().status_code == 201
        assert [item["name"] for item in alice.get("/api/workspace").json()["candidates"]] == ["Alice Candidate"]
        assert [item["name"] for item in bob.get("/api/workspace").json()["candidates"]] == ["Bob Candidate"]
