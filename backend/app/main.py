from dataclasses import asdict, replace
import os
from pathlib import Path
import re
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from .auth import AuthStore, User, WorkspaceRecord, create_auth_store
from .assistant import answer, generate_draft, generate_questions, generate_summary
from .documents import extract_document, extract_paste
from .matching import ALIASES, find_skill, rank
from .models import Candidate, JobDescription, Workspace, workspace_from_dict


class Credentials(BaseModel):
    email: str
    password: str
    keep_signed_in: bool = False


class PastedJD(BaseModel):
    title: str
    text: str
    required: list[str] | None = None
    preferred: list[str] | None = None


class PastedCandidate(BaseModel):
    name: str
    text: str


class SkillsUpdate(BaseModel):
    title: str
    required: list[str]
    preferred: list[str]


class DraftRequest(BaseModel):
    candidate_id: str
    kind: str
    date: str = ""
    time: str = ""
    link: str = ""


class DraftUpdate(BaseModel):
    text: str


class ChatRequest(BaseModel):
    question: str
    candidate_id: str | None = None


def create_app(database_url: str | None = None, secret_key: str | None = None) -> FastAPI:
    app = FastAPI(title="RoleTrace")
    app.state.auth = create_auth_store(database_url, secret_key)

    def current_user(request: Request) -> User:
        store: AuthStore = request.app.state.auth
        user = store.from_token(request.cookies.get("roletrace_session"))
        if user is None:
            raise HTTPException(status_code=401, detail="Please log in.")
        return user

    def workspace(user: User) -> Workspace:
        with app.state.auth.session_factory() as session:
            record = session.get(WorkspaceRecord, user.id)
            if record:
                return workspace_from_dict(record.payload)
            current = Workspace([], [], "")
            session.add(WorkspaceRecord(user_id=user.id, payload=asdict(current)))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                # Another first-page request created this user's workspace.
                existing = session.get(WorkspaceRecord, user.id)
                if existing is None:
                    raise
                return workspace_from_dict(existing.payload)
            return current

    def save_workspace(user: User, current: Workspace) -> None:
        with app.state.auth.session_factory() as session:
            record = session.get(WorkspaceRecord, user.id)
            if record is None:
                record = WorkspaceRecord(user_id=user.id, payload=asdict(current))
                session.add(record)
            else:
                record.payload = asdict(current)
            session.commit()

    def get_candidate(current: Workspace, candidate_id: str) -> Candidate:
        candidate = next((item for item in current.candidates if item.id == candidate_id), None)
        if candidate is None:
            raise HTTPException(status_code=404, detail="Candidate not found.")
        return candidate

    def get_jd(current: Workspace, jd_id: str) -> JobDescription:
        jd = next((item for item in current.jds if item.id == jd_id), None)
        if jd is None:
            raise HTTPException(status_code=404, detail="Job not found.")
        return jd

    def active_jd(current: Workspace) -> JobDescription:
        jd = next((item for item in current.jds if item.id == current.selected_jd_id), None)
        if jd is None:
            raise HTTPException(status_code=409, detail="Add a job description before using this feature.")
        return jd

    def inferred_skills(evidence) -> tuple[list[str], list[str]]:
        required, preferred = [], []
        section = "required"
        heading = re.compile(r"\b(required|preferred)(?:\s+(?:skills|qualifications|experience))?\s*:", re.I)

        def add_skills(chunk, text: str, target: list[str]) -> None:
            if not text.strip():
                return
            segment = replace(chunk, text=text)
            for skill in ALIASES:
                if find_skill(skill, [segment]) and skill not in target:
                    target.append(skill)

        for chunk in evidence:
            start = 0
            for marker in heading.finditer(chunk.text):
                add_skills(chunk, chunk.text[start:marker.start()], preferred if section == "preferred" else required)
                section = marker.group(1).lower()
                start = marker.end()
            add_skills(chunk, chunk.text[start:], preferred if section == "preferred" else required)
        return required, preferred

    def set_cookie(response: Response, store: AuthStore, user: User, remember: bool) -> None:
        response.set_cookie(
            "roletrace_session",
            store.sign(user.id, remember),
            httponly=True,
            secure=os.getenv("APP_ENV") == "production",
            samesite="lax",
            max_age=7 * 86400 if remember else None,
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/auth/register", status_code=201)
    def register(body: Credentials, response: Response, request: Request):
        store: AuthStore = request.app.state.auth
        try:
            user = store.register(body.email, body.password)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if user is None:
            raise HTTPException(status_code=409, detail="Account could not be created. Try logging in.")
        set_cookie(response, store, user, body.keep_signed_in)
        return {"id": user.id, "email": user.email}

    @app.post("/api/auth/login")
    def login(body: Credentials, response: Response, request: Request):
        store: AuthStore = request.app.state.auth
        user = store.authenticate(body.email, body.password)
        if user is None:
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        set_cookie(response, store, user, body.keep_signed_in)
        return {"id": user.id, "email": user.email}

    @app.get("/api/auth/me")
    def me(user: User = Depends(current_user)):
        return {"id": user.id, "email": user.email}

    @app.post("/api/auth/logout")
    def logout(response: Response):
        response.delete_cookie("roletrace_session", samesite="lax")
        return {"ok": True}

    @app.get("/api/workspace")
    def get_workspace(user: User = Depends(current_user)):
        current = workspace(user)
        return {
            "jds": [asdict(item) for item in current.jds],
            "candidates": [asdict(item) for item in current.candidates],
            "selected_jd_id": current.selected_jd_id,
            "recruitment": current.recruitment,
            "drafts": current.drafts,
        }

    @app.delete("/api/workspace/sample-data")
    def remove_sample_data(user: User = Depends(current_user)):
        current = workspace(user)
        bundled_jds = {"data-engineer", "fullstack"}
        bundled_candidates = {"maya", "arjun", "neha", "samira", "dev", "lena"}
        current.jds = [jd for jd in current.jds if jd.id not in bundled_jds]
        current.candidates = [candidate for candidate in current.candidates if candidate.id not in bundled_candidates]
        current.recruitment = [item for item in current.recruitment if item["candidate_id"] not in bundled_candidates]
        current.drafts = [item for item in current.drafts if item["candidate_id"] not in bundled_candidates]
        if current.selected_jd_id in bundled_jds:
            current.selected_jd_id = current.jds[0].id if current.jds else ""
        save_workspace(user, current)
        return {"ok": True}

    @app.post("/api/jds/paste", status_code=201)
    def add_pasted_jd(body: PastedJD, user: User = Depends(current_user)):
        current = workspace(user)
        try:
            evidence = extract_paste(body.text)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        inferred_required, inferred_preferred = inferred_skills(evidence)
        jd = JobDescription(uuid4().hex, body.title.strip() or "Untitled job", body.required if body.required is not None else inferred_required, body.preferred if body.preferred is not None else inferred_preferred, evidence)
        current.jds.append(jd)
        current.selected_jd_id = jd.id
        save_workspace(user, current)
        return asdict(jd)

    @app.post("/api/jds/upload", status_code=201)
    async def add_uploaded_jd(file: UploadFile = File(...), user: User = Depends(current_user)):
        current = workspace(user)
        try:
            evidence = extract_document(file.filename or "job.txt", await file.read())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        required, preferred = inferred_skills(evidence)
        jd = JobDescription(uuid4().hex, Path(file.filename or "Job").stem.replace("_", " "), required, preferred, evidence)
        current.jds.append(jd)
        current.selected_jd_id = jd.id
        save_workspace(user, current)
        return asdict(jd)

    @app.post("/api/jds/{jd_id}/select")
    def select_jd(jd_id: str, user: User = Depends(current_user)):
        current = workspace(user)
        get_jd(current, jd_id)
        current.selected_jd_id = jd_id
        save_workspace(user, current)
        return {"selected_jd_id": jd_id}

    @app.patch("/api/jds/{jd_id}")
    def update_jd(jd_id: str, body: SkillsUpdate, user: User = Depends(current_user)):
        current = workspace(user)
        jd = get_jd(current, jd_id)
        jd.title = body.title.strip() or jd.title
        jd.required = [item.strip() for item in body.required if item.strip()]
        jd.preferred = [item.strip() for item in body.preferred if item.strip()]
        save_workspace(user, current)
        return asdict(jd)

    @app.post("/api/candidates/paste", status_code=201)
    def add_pasted_candidate(body: PastedCandidate, user: User = Depends(current_user)):
        current = workspace(user)
        try:
            evidence = extract_paste(body.text)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        candidate = Candidate(uuid4().hex, body.name.strip() or "Unnamed candidate", evidence)
        current.candidates.append(candidate)
        save_workspace(user, current)
        return asdict(candidate)

    @app.post("/api/candidates/upload", status_code=201)
    async def add_uploaded_candidate(file: UploadFile = File(...), user: User = Depends(current_user)):
        current = workspace(user)
        try:
            evidence = extract_document(file.filename or "resume.txt", await file.read())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        candidate = Candidate(uuid4().hex, Path(file.filename or "Candidate").stem.replace("_", " "), evidence)
        current.candidates.append(candidate)
        save_workspace(user, current)
        return asdict(candidate)

    @app.delete("/api/candidates/{candidate_id}")
    def remove_candidate(candidate_id: str, user: User = Depends(current_user)):
        current = workspace(user)
        get_candidate(current, candidate_id)
        current.candidates = [item for item in current.candidates if item.id != candidate_id]
        save_workspace(user, current)
        return {"ok": True}

    @app.get("/api/compare")
    def compare(user: User = Depends(current_user)):
        current = workspace(user)
        jd = next((item for item in current.jds if item.id == current.selected_jd_id), None)
        return {"jd": asdict(jd) if jd else None, "results": [asdict(item) for item in rank(jd, current.candidates)] if jd else []}

    @app.get("/api/candidates/{candidate_id}/analysis")
    def candidate_analysis(candidate_id: str, user: User = Depends(current_user)):
        current = workspace(user)
        candidate = get_candidate(current, candidate_id)
        jd = active_jd(current)
        match = next(item for item in rank(jd, current.candidates) if item.candidate_id == candidate_id)
        return {"candidate": asdict(candidate), "jd": asdict(jd), "match": asdict(match), "summary": generate_summary(jd, candidate, match), "questions": generate_questions(jd, candidate, match)}

    @app.post("/api/drafts/generate")
    def create_draft(body: DraftRequest, user: User = Depends(current_user)):
        current = workspace(user)
        candidate = get_candidate(current, body.candidate_id)
        jd = active_jd(current)
        try:
            content = generate_draft(body.kind, jd, candidate, body.date, body.time, body.link)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        draft = {"id": uuid4().hex, "candidate_id": candidate.id, "candidate_name": candidate.name, "job_title": jd.title, "kind": body.kind, "text": content}
        current.drafts.append(draft)
        save_workspace(user, current)
        return draft

    @app.patch("/api/drafts/{draft_id}")
    def update_draft(draft_id: str, body: DraftUpdate, user: User = Depends(current_user)):
        current = workspace(user)
        draft = next((item for item in current.drafts if item["id"] == draft_id), None)
        if draft is None:
            raise HTTPException(status_code=404, detail="Draft not found.")
        draft["text"] = body.text
        save_workspace(user, current)
        return draft

    @app.delete("/api/drafts/{draft_id}")
    def delete_draft(draft_id: str, user: User = Depends(current_user)):
        current = workspace(user)
        old = len(current.drafts)
        current.drafts = [item for item in current.drafts if item["id"] != draft_id]
        if len(current.drafts) == old:
            raise HTTPException(status_code=404, detail="Draft not found.")
        save_workspace(user, current)
        return {"ok": True}

    @app.post("/api/chat")
    def chat(body: ChatRequest, user: User = Depends(current_user)):
        current = workspace(user)
        question = body.question.strip()
        if not question:
            raise HTTPException(status_code=422, detail="Enter a question.")
        if body.candidate_id:
            candidate = get_candidate(current, body.candidate_id)
            if candidate.name.lower() not in question.lower():
                question = f"About {candidate.name}: {question}"
        return answer(question, current)

    frontend = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if (frontend / "index.html").exists() and (frontend / "assets").exists():
        app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")

        @app.get("/{path:path}")
        def serve_frontend(path: str):
            if path.startswith(("api/", "assets/")):
                raise HTTPException(status_code=404, detail="Not found.")
            target = frontend / path
            if path and target.is_file() and target.resolve().is_relative_to(frontend.resolve()):
                return FileResponse(target)
            return FileResponse(frontend / "index.html")

    return app


app = create_app()
