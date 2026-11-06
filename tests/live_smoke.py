"""Run synthetic end-to-end checks against an explicitly supplied RoleTrace URL.

Usage: python tests/live_smoke.py https://roletrace.vercel.app
Creates two disposable synthetic accounts. Requires curl and project dependencies.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
from pathlib import Path
import secrets
import subprocess
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

from docx import Document
from reportlab.pdfgen import canvas


def request(base_url, cookies, method, path, *, body=None, upload=None):
    command = ["curl", "-sS", "--max-time", "35", "-b", str(cookies), "-c", str(cookies), "-w", "\n%{http_code}", "-X", method]
    if body is not None:
        command += ["-H", "Content-Type: application/json", "--data-binary", json.dumps(body)]
    if upload is not None:
        command += ["-F", f"file=@{upload}"]
    command.append(base_url.rstrip("/") + path)
    for attempt in range(3):
        result = subprocess.run(command, capture_output=True, text=True)
        if not result.returncode:
            break
        # DNS, connection, and TLS-handshake errors occur before a request is sent.
        safe_to_retry = result.returncode in {6, 7, 35} or (method == "GET" and result.returncode == 28)
        if safe_to_retry and attempt < 2:
            time.sleep(0.5 * (attempt + 1))
            continue
        raise RuntimeError(f"curl failed for {method} {path}: {result.stderr[:300]}")
    payload, separator, status = result.stdout.rpartition("\n")
    if not separator:
        raise AssertionError(f"No HTTP status for {method} {path}: {result.stderr[:300]}")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = {"raw": payload[:300]}
    return int(status), data


def expect(response, status, label):
    actual, data = response
    if actual != status:
        raise AssertionError(f"{label}: expected {status}, got {actual}: {str(data)[:300]}")
    return data


def make_pdf(path):
    output = BytesIO()
    pdf = canvas.Canvas(output)
    pdf.drawString(72, 720, "Built Python and SQL pipelines using Airflow and AWS.")
    pdf.showPage()
    pdf.save()
    path.write_bytes(output.getvalue())


def make_docx(path):
    document = Document()
    document.add_paragraph("Required: React, TypeScript, and FastAPI. Preferred: Docker.")
    document.save(path)


def run(base_url):
    checks = []
    with TemporaryDirectory(prefix="roletrace-qa-") as directory:
        root = Path(directory)
        alice_cookie, bob_cookie, guest_cookie = (root / name for name in ("alice.cookies", "bob.cookies", "guest.cookies"))
        for cookie in (alice_cookie, bob_cookie, guest_cookie):
            cookie.touch()
        password = secrets.token_urlsafe(20)
        suffix = uuid4().hex[:12]
        alice_email = f"qa-alice-{suffix}@example.test"
        bob_email = f"qa-bob-{suffix}@example.test"

        expect(request(base_url, guest_cookie, "GET", "/health"), 200, "health")
        expect(request(base_url, guest_cookie, "GET", "/api/workspace"), 401, "private workspace")
        checks.append("health and private endpoints")

        for cookie, email in ((alice_cookie, alice_email), (bob_cookie, bob_email)):
            expect(request(base_url, cookie, "POST", "/api/auth/register", body={"email": email, "password": password}), 201, "register")
            empty = expect(request(base_url, cookie, "GET", "/api/workspace"), 200, "fresh workspace")
            assert empty["jds"] == empty["candidates"] == [] and empty["drafts"] == []
            comparison = expect(request(base_url, cookie, "GET", "/api/compare"), 200, "empty comparison")
            assert comparison == {"jd": None, "results": []}
        checks.append("two fresh, separate accounts start empty")

        empty_chat = expect(request(base_url, alice_cookie, "POST", "/api/chat", body={"question": "Who is the top match?"}), 200, "empty chat")
        assert "job description" in empty_chat["text"].lower() and empty_chat["citations"] == []
        expect(request(base_url, guest_cookie, "POST", "/api/auth/login", body={"email": alice_email, "password": "wrong-password"}), 401, "bad password")
        expect(request(base_url, guest_cookie, "POST", "/api/auth/register", body={"email": alice_email, "password": password}), 409, "duplicate email")
        checks.append("empty guidance and account errors")

        sample_dir = Path(__file__).resolve().parents[1] / "sample_data"
        jd = expect(request(base_url, alice_cookie, "POST", "/api/jds/upload", upload=sample_dir / "senior_data_engineer_jd.txt"), 201, "upload JD")
        maya = expect(request(base_url, alice_cookie, "POST", "/api/candidates/upload", upload=sample_dir / "maya_shah_cv.txt"), 201, "upload TXT CV")
        arjun = expect(request(base_url, alice_cookie, "POST", "/api/candidates/upload", upload=sample_dir / "arjun_rao_cv.txt"), 201, "upload second TXT CV")
        comparison = expect(request(base_url, alice_cookie, "GET", "/api/compare"), 200, "rank candidates")
        assert comparison["jd"]["id"] == jd["id"]
        assert len(comparison["results"]) == 2
        assert comparison["results"][0]["candidate_id"] == maya["id"]
        assert comparison["results"][0]["score"] > comparison["results"][1]["score"]
        analysis = expect(request(base_url, alice_cookie, "GET", f"/api/candidates/{maya['id']}/analysis"), 200, "analysis")
        assert analysis["summary"] and analysis["questions"] and analysis["match"]["evidence"]
        reply = expect(request(base_url, alice_cookie, "POST", "/api/chat", body={"question": "Why is Maya a match?", "candidate_id": maya["id"]}), 200, "grounded chat")
        assert reply["citations"]
        unknown = expect(request(base_url, alice_cookie, "POST", "/api/chat", body={"question": "Does Maya have a certification?", "candidate_id": maya["id"]}), 200, "unknown fact")
        assert "not established" in unknown["text"].lower()
        checks.append("TXT uploads, ranking, evidence, interview prep, grounded chat")

        unrecorded = expect(request(base_url, alice_cookie, "POST", "/api/chat", body={"question": "What stage is Maya at?", "candidate_id": maya["id"]}), 200, "unknown stage")
        assert "not recorded" in unrecorded["text"].lower()
        stage = expect(request(base_url, alice_cookie, "PATCH", f"/api/candidates/{maya['id']}/recruitment", body={"stage": "Recruiter screen", "assessment": "Data exercise pending"}), 200, "save stage")
        assert stage["stage"] == "Recruiter screen"
        known_stage = expect(request(base_url, alice_cookie, "POST", "/api/chat", body={"question": "What assessment is Maya assigned?", "candidate_id": maya["id"]}), 200, "recorded stage")
        assert "Data exercise pending" in known_stage["text"] and known_stage["citations"][0]["source"] == "Recruitment record"
        checks.append("recruitment status is editable and chat reports only saved facts")

        invitation = expect(request(base_url, alice_cookie, "POST", "/api/drafts/generate", body={"candidate_id": maya["id"], "kind": "invitation", "date": "2026-11-10", "time": "14:00", "link": "https://example.test/meet"}), 200, "invitation")
        assessment = expect(request(base_url, alice_cookie, "POST", "/api/drafts/generate", body={"candidate_id": maya["id"], "kind": "assessment", "date": "2026-11-12", "link": "https://example.test/task"}), 200, "assessment")
        assert "Interview invitation" in invitation["text"] and "Assessment instructions" in assessment["text"]
        edited = expect(request(base_url, alice_cookie, "PATCH", f"/api/drafts/{invitation['id']}", body={"text": "Edited synthetic invitation"}), 200, "edit draft")
        assert edited["text"] == "Edited synthetic invitation"
        checks.append("invitation and assessment drafts, editing")

        bob = expect(request(base_url, bob_cookie, "GET", "/api/workspace"), 200, "Bob workspace")
        assert bob["jds"] == bob["candidates"] == bob["drafts"] == []
        expect(request(base_url, bob_cookie, "GET", f"/api/candidates/{maya['id']}/analysis"), 404, "cross-account candidate")
        expect(request(base_url, bob_cookie, "POST", f"/api/jds/{jd['id']}/select"), 404, "cross-account JD")
        expect(request(base_url, bob_cookie, "PATCH", f"/api/drafts/{invitation['id']}", body={"text": "Wrong account"}), 404, "cross-account draft")
        expect(request(base_url, bob_cookie, "PATCH", f"/api/candidates/{maya['id']}/recruitment", body={"stage": "Offer"}), 404, "cross-account status")
        checks.append("cross-account resource access denied")

        docx_path, pdf_path = root / "full_stack.docx", root / "Synthetic_PDF_Candidate.pdf"
        make_docx(docx_path)
        make_pdf(pdf_path)
        bob_jd = expect(request(base_url, bob_cookie, "POST", "/api/jds/upload", upload=docx_path), 201, "DOCX JD")
        bob_cv = expect(request(base_url, bob_cookie, "POST", "/api/candidates/upload", upload=pdf_path), 201, "PDF CV")
        assert bob_jd["required"] and bob_cv["evidence"][0]["location"] == "page 1"
        assert len(expect(request(base_url, bob_cookie, "GET", "/api/compare"), 200, "Bob comparison")["results"]) == 1
        assert len(expect(request(base_url, alice_cookie, "GET", "/api/compare"), 200, "Alice comparison")["results"]) == 2
        checks.append("DOCX and PDF extraction and isolated comparison")

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(request, base_url, alice_cookie, "POST", "/api/candidates/paste", body={"name": "Alice Concurrent", "text": "Python and SQL"})
            second = pool.submit(request, base_url, bob_cookie, "POST", "/api/candidates/paste", body={"name": "Bob Concurrent", "text": "React and TypeScript"})
            expect(first.result(), 201, "Alice concurrent write")
            expect(second.result(), 201, "Bob concurrent write")
        alice_names = [item["name"] for item in expect(request(base_url, alice_cookie, "GET", "/api/workspace"), 200, "Alice after writes")["candidates"]]
        bob_names = [item["name"] for item in expect(request(base_url, bob_cookie, "GET", "/api/workspace"), 200, "Bob after writes")["candidates"]]
        assert "Alice Concurrent" in alice_names and "Bob Concurrent" not in alice_names
        assert "Bob Concurrent" in bob_names and "Alice Concurrent" not in bob_names
        checks.append("simultaneous writes stay in separate workspaces")

        invalid_path = root / "bad.png"
        invalid_path.write_bytes(b"not an image")
        expect(request(base_url, alice_cookie, "POST", "/api/candidates/upload", upload=invalid_path), 422, "invalid file")
        expect(request(base_url, alice_cookie, "POST", "/api/candidates/paste", body={"name": "Empty", "text": "  "}), 422, "empty CV")
        oversized_path = root / "too_large.txt"
        oversized_path.write_bytes(b"x" * (4 * 1024 * 1024 + 1))
        expect(request(base_url, alice_cookie, "POST", "/api/candidates/upload", upload=oversized_path), 422, "oversized file")
        checks.append("invalid and oversized document errors")

        expect(request(base_url, alice_cookie, "DELETE", f"/api/drafts/{invitation['id']}"), 200, "delete draft")
        expect(request(base_url, alice_cookie, "DELETE", f"/api/candidates/{arjun['id']}"), 200, "delete candidate")
        expect(request(base_url, alice_cookie, "POST", "/api/auth/logout"), 200, "logout")
        expect(request(base_url, alice_cookie, "GET", "/api/workspace"), 401, "logged-out workspace")
        expect(request(base_url, alice_cookie, "POST", "/api/auth/login", body={"email": alice_email, "password": password}), 200, "login")
        restored = expect(request(base_url, alice_cookie, "GET", "/api/workspace"), 200, "persistent workspace")
        assert len(restored["jds"]) == 1 and len(restored["candidates"]) == 2 and len(restored["drafts"]) == 1
        checks.append("delete, logout, login, Neon persistence")

        long_cv = expect(request(base_url, alice_cookie, "POST", "/api/candidates/paste", body={"name": "Long Synthetic CV", "text": "Background: " + "x" * 400_000 + " Built Python and SQL pipelines with Airflow."}), 201, "long CV")
        assert len(json.dumps(long_cv)) < 100_000
        assert len(json.dumps(expect(request(base_url, alice_cookie, "GET", "/api/workspace"), 200, "compact workspace"))) < 100_000
        ranked = expect(request(base_url, alice_cookie, "GET", "/api/compare"), 200, "compact comparison")
        assert len(json.dumps(ranked)) < 100_000
        assert "Python" in next(row for row in ranked["results"] if row["candidate_id"] == long_cv["id"])["evidence"]["Python"]["text"]
        checks.append("large CV responses stay compact with relevant evidence")

    return checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="Explicit RoleTrace base URL; creates two synthetic test accounts")
    args = parser.parse_args()
    completed = run(args.base_url)
    print(json.dumps({"result": "passed", "checks": completed}, indent=2))
