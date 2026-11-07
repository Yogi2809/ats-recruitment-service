from dataclasses import asdict
from datetime import datetime, timezone
import os
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError

from .auth import AuthStore, User, WorkspaceRecord, StoredDocument, SharedDocument, create_auth_store
from .assistant import answer, generate_draft, generate_questions, generate_summary
from .documents import extract_document, extract_paste
from .matching import rank
from .models import Candidate, JobDescription, Workspace, workspace_from_dict
from .serializers import candidate_response, jd_response, match_response
from .skill_extraction import analyze_jd


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


class JDMetadata(BaseModel):
    department: str


class CandidateMetadata(BaseModel):
    tags: list[str]


class SkillsUpdate(BaseModel):
    title: str
    required: list[str]
    preferred: list[str]


class SkillsPreview(BaseModel):
    selected_role: str | None = None


class SkillsSave(BaseModel):
    selected_role: str | None = None
    requirements: list[dict]


class DraftRequest(BaseModel):
    candidate_id: str
    kind: str
    date: str = ""
    time: str = ""
    link: str = ""


class DraftUpdate(BaseModel):
    text: str


class RecruitmentUpdate(BaseModel):
    stage: str
    assessment: str = ""


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
        revision_header = request.headers.get("X-Workspace-Revision")
        if revision_header is not None:
            if not revision_header.isascii() or not revision_header.isdigit() or len(revision_header) > 12:
                raise HTTPException(status_code=400, detail="Invalid workspace version.")
            user._workspace_revision = int(revision_header)
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

    def save_workspace(user: User, current: Workspace, extra=None) -> None:
        previous_revision = current.revision
        client_revision = getattr(user, "_workspace_revision", None)
        if client_revision is not None and client_revision != previous_revision:
            raise HTTPException(status_code=409, detail="Your workspace changed in another session. Refresh and try this action again.")
        current.revision += 1
        with app.state.auth.session_factory() as session:
            result = session.execute(
                update(WorkspaceRecord)
                .where(WorkspaceRecord.user_id == user.id,
                       func.coalesce(WorkspaceRecord.payload["revision"].as_integer(), 0) == previous_revision)
                .values(payload=asdict(current))
            )
            if result.rowcount != 1:
                session.rollback()
                raise HTTPException(status_code=409, detail="Your workspace changed in another session. Refresh and try this action again.")
            if extra is not None:
                extra(session)
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
            raise HTTPException(status_code=409, detail="This email is already registered. Log in instead.")
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
            "revision": current.revision,
            "jds": [jd_response(item) for item in current.jds],
            "candidates": [candidate_response(item) for item in current.candidates],
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
        def remove_files(session):
            session.execute(delete(SharedDocument).where(SharedDocument.user_id == user.id, SharedDocument.source_id.in_(bundled_jds | bundled_candidates)))
            session.execute(delete(StoredDocument).where(StoredDocument.user_id == user.id, StoredDocument.id.in_(bundled_jds | bundled_candidates)))
        save_workspace(user, current, remove_files)
        return {"ok": True}

    @app.post("/api/jds/paste", status_code=201)
    def add_pasted_jd(body: PastedJD, user: User = Depends(current_user)):
        current = workspace(user)
        try:
            evidence = extract_paste(body.text)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        jd = JobDescription(uuid4().hex, body.title.strip() or "Untitled job", body.required or [], body.preferred or [], evidence, extractor_version="2")
        current.jds.append(jd)
        current.selected_jd_id = jd.id
        save_workspace(user, current, lambda session: session.add(StoredDocument(id=jd.id, user_id=user.id, filename='job-description.txt', contents=body.text.encode('utf-8'))))
        return jd_response(jd, include_evidence=True)

    @app.post("/api/jds/upload", status_code=201)
    async def add_uploaded_jd(file: UploadFile = File(...), user: User = Depends(current_user)):
        current = workspace(user)
        try:
            raw = await file.read()
            evidence = extract_document(file.filename or "job.txt", raw)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        jd = JobDescription(uuid4().hex, Path(file.filename or "Job").stem.replace("_", " "), [], [], evidence, extractor_version="2")
        current.jds.append(jd)
        current.selected_jd_id = jd.id
        save_workspace(user, current, lambda session: session.add(StoredDocument(id=jd.id, user_id=user.id, filename=Path(file.filename or 'job.txt').name[:255], contents=raw)))
        return jd_response(jd, include_evidence=True)

    @app.post("/api/jds/{jd_id}/select")
    def select_jd(jd_id: str, user: User = Depends(current_user)):
        current = workspace(user)
        get_jd(current, jd_id)
        current.selected_jd_id = jd_id
        save_workspace(user, current)
        return {"selected_jd_id": jd_id}

    @app.get('/api/jds/{jd_id}')
    def view_jd(jd_id: str, user: User = Depends(current_user)):
        return asdict(get_jd(workspace(user), jd_id))

    @app.delete("/api/jds/{jd_id}")
    def remove_jd(jd_id: str, user: User = Depends(current_user)):
        current = workspace(user)
        get_jd(current, jd_id)
        current.jds = [item for item in current.jds if item.id != jd_id]
        if current.selected_jd_id == jd_id:
            current.selected_jd_id = current.jds[0].id if current.jds else ""
        def remove_files(session):
            session.execute(delete(SharedDocument).where(SharedDocument.user_id == user.id, SharedDocument.kind == 'jd', SharedDocument.source_id == jd_id))
            session.execute(delete(StoredDocument).where(StoredDocument.user_id == user.id, StoredDocument.id == jd_id))
        save_workspace(user, current, remove_files)
        return {"ok": True}

    @app.patch("/api/jds/{jd_id}/metadata")
    def update_jd_metadata(jd_id: str, body: JDMetadata, user: User = Depends(current_user)):
        current = workspace(user)
        jd = get_jd(current, jd_id)
        department = body.department.strip()
        if not department or len(department) > 60:
            raise HTTPException(status_code=422, detail="Enter a department of up to 60 characters.")
        jd.department = department
        save_workspace(user, current)
        return jd_response(jd)

    @app.patch("/api/jds/{jd_id}")
    def update_jd(jd_id: str, body: SkillsUpdate, user: User = Depends(current_user)):
        current = workspace(user)
        jd = get_jd(current, jd_id)
        jd.title = body.title.strip() or jd.title
        jd.required = [item.strip() for item in body.required if item.strip()]
        jd.preferred = [item.strip() for item in body.preferred if item.strip()]
        jd.reviewed_requirements = [
            {"id": uuid4().hex, "label": label, "kind": "skill", "category": category,
             "options": [label], "source_id": "", "source_location": "", "source_quote": "",
             "source_section": "", "origin": "manual"}
            for category, labels in (("required", jd.required), ("preferred", jd.preferred))
            for label in labels
        ]
        jd.reviewed_at = datetime.now(timezone.utc).isoformat()
        jd.extractor_version = "2"
        save_workspace(user, current)
        return jd_response(jd, include_evidence=True)

    @app.post("/api/jds/{jd_id}/skills/preview")
    def preview_jd_skills(jd_id: str, body: SkillsPreview, user: User = Depends(current_user)):
        current = workspace(user)
        jd = get_jd(current, jd_id)
        try:
            preview = analyze_jd(jd.evidence, body.selected_role)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {**preview, "current_required": jd.required, "current_preferred": jd.preferred,
                "needs_review": jd.reviewed_at is None}

    @app.put("/api/jds/{jd_id}/skills")
    def save_jd_skills(jd_id: str, body: SkillsSave, user: User = Depends(current_user)):
        current = workspace(user)
        jd = get_jd(current, jd_id)
        try:
            preview = analyze_jd(jd.evidence, body.selected_role)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if preview["roles"] and preview["selected_role"] is None:
            raise HTTPException(status_code=422, detail="Choose one role before saving skills.")
        if len(body.requirements) > 100:
            raise HTTPException(status_code=422, detail="Use no more than 100 requirements.")
        offered = {item["id"]: item for item in preview["suggestions"]}
        approved = []
        used_labels = set()
        for raw in body.requirements:
            if not isinstance(raw, dict):
                raise HTTPException(status_code=422, detail="Invalid skill entry.")
            label = raw.get("label")
            category = raw.get("category")
            kind = raw.get("kind")
            origin = raw.get("origin")
            options = raw.get("options")
            if not isinstance(label, str) or not label.strip() or len(label.strip()) > 100 or category not in {"required", "preferred", "unspecified"} or kind not in {"skill", "other_requirement"} or origin not in {"suggested", "manual"} or not isinstance(options, list) or not 1 <= len(options) <= 8 or any(not isinstance(value, str) or not value.strip() or len(value) > 100 for value in options):
                raise HTTPException(status_code=422, detail="Check each skill label, category, and alternative.")
            label = label.strip()
            if label.casefold() in used_labels:
                raise HTTPException(status_code=422, detail="Remove duplicate skills before saving.")
            used_labels.add(label.casefold())
            if origin == "suggested":
                source = offered.get(raw.get("id"))
                if source is None or label != source["label"] or options != source["options"] or raw.get("source_id") != source["source_id"]:
                    raise HTTPException(status_code=422, detail="A suggested skill no longer matches this JD. Reanalyse it or mark your edit as manual.")
                approved.append({**source, "category": category, "kind": kind})
            else:
                approved.append({"id": uuid4().hex, "label": label, "kind": kind, "category": category,
                                 "options": [value.strip() for value in options], "source_id": "",
                                 "source_location": "", "source_quote": "", "source_section": "",
                                 "origin": "manual"})
        jd.reviewed_requirements = approved
        jd.required = [item["label"] for item in approved if item["kind"] == "skill" and item["category"] == "required"]
        jd.preferred = [item["label"] for item in approved if item["kind"] == "skill" and item["category"] == "preferred"]
        jd.selected_role = preview["selected_role"]
        jd.extractor_version = "2"
        jd.reviewed_at = datetime.now(timezone.utc).isoformat()
        save_workspace(user, current)
        return jd_response(jd, include_evidence=True)

    @app.post("/api/candidates/paste", status_code=201)
    def add_pasted_candidate(body: PastedCandidate, user: User = Depends(current_user)):
        current = workspace(user)
        try:
            evidence = extract_paste(body.text)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        candidate = Candidate(uuid4().hex, body.name.strip() or "Unnamed candidate", evidence)
        current.candidates.append(candidate)
        save_workspace(user, current, lambda session: session.add(StoredDocument(id=candidate.id, user_id=user.id, filename='candidate-cv.txt', contents=body.text.encode('utf-8'))))
        return candidate_response(candidate, include_evidence=True)

    @app.post("/api/candidates/upload", status_code=201)
    async def add_uploaded_candidate(file: UploadFile = File(...), user: User = Depends(current_user)):
        current = workspace(user)
        try:
            raw = await file.read()
            evidence = extract_document(file.filename or "resume.txt", raw)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        candidate = Candidate(uuid4().hex, Path(file.filename or "Candidate").stem.replace("_", " "), evidence)
        current.candidates.append(candidate)
        save_workspace(user, current, lambda session: session.add(StoredDocument(id=candidate.id, user_id=user.id, filename=Path(file.filename or 'resume.txt').name[:255], contents=raw)))
        return candidate_response(candidate, include_evidence=True)

    @app.delete("/api/candidates/{candidate_id}")
    def remove_candidate(candidate_id: str, user: User = Depends(current_user)):
        current = workspace(user)
        get_candidate(current, candidate_id)
        current.candidates = [item for item in current.candidates if item.id != candidate_id]
        current.recruitment = [item for item in current.recruitment if item["candidate_id"] != candidate_id]
        def remove_files(session):
            session.execute(delete(SharedDocument).where(SharedDocument.user_id == user.id, SharedDocument.kind == 'candidate', SharedDocument.source_id == candidate_id))
            session.execute(delete(StoredDocument).where(StoredDocument.user_id == user.id, StoredDocument.id == candidate_id))
        save_workspace(user, current, remove_files)
        return {"ok": True}

    @app.get('/api/candidates/{candidate_id}')
    def view_candidate(candidate_id: str, user: User = Depends(current_user)):
        return asdict(get_candidate(workspace(user), candidate_id))

    @app.patch("/api/candidates/{candidate_id}/metadata")
    def update_candidate_metadata(candidate_id: str, body: CandidateMetadata, user: User = Depends(current_user)):
        current = workspace(user)
        candidate = get_candidate(current, candidate_id)
        tags = [tag.strip() for tag in body.tags]
        if len(tags) > 20 or any(not tag or len(tag) > 40 for tag in tags) or len({tag.casefold() for tag in tags}) != len(tags):
            raise HTTPException(status_code=422, detail="Use up to 20 unique tags, each 1–40 characters.")
        candidate.tags = tags
        save_workspace(user, current)
        return candidate_response(candidate)

    @app.get('/api/library')
    def list_shared(user: User = Depends(current_user)):
        with app.state.auth.session_factory() as session:
            rows = session.execute(select(SharedDocument.id, SharedDocument.user_id, SharedDocument.kind, SharedDocument.snapshot, SharedDocument.filename)).all()
            return {'items': [{'id': row.id, 'kind': row.kind, 'title': row.snapshot.get('title') or row.snapshot.get('name'),
                               'department': row.snapshot.get('department', 'Unassigned'), 'tags': row.snapshot.get('tags', []),
                               'owned': row.user_id == user.id, 'download_available': row.filename is not None,
                               'download_is_extracted': row.filename == 'extracted-text.txt'} for row in rows]}

    @app.post('/api/library/share/{kind}/{source_id}', status_code=201)
    def share_document(kind: str, source_id: str, user: User = Depends(current_user)):
        current = workspace(user)
        if kind not in {'jd', 'candidate'}:
            raise HTTPException(status_code=404, detail='Document not found.')
        source = get_jd(current, source_id) if kind == 'jd' else get_candidate(current, source_id)
        shared_id = uuid4().hex
        def publish(session):
            existing = session.scalar(select(SharedDocument.id).where(SharedDocument.user_id == user.id, SharedDocument.kind == kind, SharedDocument.source_id == source_id))
            if existing:
                raise HTTPException(status_code=409, detail='This document is already shared.')
            original = session.get(StoredDocument, source_id)
            pasted = source.evidence and all(item.source == 'Pasted text' for item in source.evidence)
            filename = original.filename if original and original.user_id == user.id else ('extracted-text.txt' if pasted else None)
            contents = original.contents if original and original.user_id == user.id else ('\n'.join(e.text for e in source.evidence).encode('utf-8') if pasted else None)
            session.add(SharedDocument(id=shared_id, user_id=user.id, kind=kind, source_id=source_id, snapshot=asdict(source), filename=filename, contents=contents))
        try:
            save_workspace(user, current, publish)
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail='This document is already shared.') from exc
        return {'id': shared_id}

    @app.get('/api/library/{shared_id}')
    def view_shared(shared_id: str, user: User = Depends(current_user)):
        with app.state.auth.session_factory() as session:
            item = session.get(SharedDocument, shared_id)
            if item is None:
                raise HTTPException(status_code=404, detail='Shared document not found.')
            return {'id': item.id, 'kind': item.kind, 'document': item.snapshot, 'owned': item.user_id == user.id, 'download_available': item.filename is not None}

    @app.get('/api/library/{shared_id}/download')
    def download_shared(shared_id: str, user: User = Depends(current_user)):
        with app.state.auth.session_factory() as session:
            item = session.get(SharedDocument, shared_id)
            if item is None:
                raise HTTPException(status_code=404, detail='Shared document not found.')
            if item.contents is None or item.filename is None:
                raise HTTPException(status_code=404, detail='Original file is unavailable for this older document.')
            return Response(content=item.contents, media_type='application/octet-stream', headers={'Content-Disposition': f"attachment; filename*=UTF-8''{quote(item.filename, safe='')}"})

    @app.delete('/api/library/{shared_id}')
    def unshare_document(shared_id: str, user: User = Depends(current_user)):
        with app.state.auth.session_factory() as session:
            item = session.get(SharedDocument, shared_id)
            if item is None or item.user_id != user.id:
                raise HTTPException(status_code=404, detail='Shared document not found.')
            session.delete(item)
            session.commit()
        return {'ok': True}

    @app.post('/api/library/{shared_id}/copy')
    def copy_shared(shared_id: str, user: User = Depends(current_user)):
        current = workspace(user)
        with app.state.auth.session_factory() as session:
            item = session.get(SharedDocument, shared_id)
            if item is None:
                raise HTTPException(status_code=404, detail='Shared document not found.')
            kind, snapshot, filename, contents = item.kind, item.snapshot, item.filename, item.contents
        new_id = uuid4().hex
        snapshot = {**snapshot, 'id': new_id}
        temp = workspace_from_dict({'jds': [snapshot] if kind == 'jd' else [], 'candidates': [snapshot] if kind == 'candidate' else [], 'selected_jd_id': ''})
        if kind == 'jd':
            source = temp.jds[0]
            current.jds.append(source)
            current.selected_jd_id = source.id
        else:
            source = temp.candidates[0]
            current.candidates.append(source)
        def copy_file(session):
            if session.get(SharedDocument, shared_id, with_for_update=True) is None:
                raise HTTPException(status_code=404, detail='This document is no longer shared.')
            if filename is not None and contents is not None:
                session.add(StoredDocument(id=new_id, user_id=user.id, filename=filename, contents=contents))
        save_workspace(user, current, copy_file)
        return jd_response(source) if kind == 'jd' else candidate_response(source)

    @app.patch("/api/candidates/{candidate_id}/recruitment")
    def update_recruitment(candidate_id: str, body: RecruitmentUpdate, user: User = Depends(current_user)):
        current = workspace(user)
        get_candidate(current, candidate_id)
        stage = body.stage.strip()
        assessment = body.assessment.strip()
        if not stage or len(stage) > 80 or len(assessment) > 500:
            raise HTTPException(status_code=422, detail="Enter a stage (up to 80 characters) and an assessment note up to 500 characters.")
        record = next((item for item in current.recruitment if item["candidate_id"] == candidate_id), None)
        if record is None:
            record = {"candidate_id": candidate_id, "stage": stage, "assessment": assessment}
            current.recruitment.append(record)
        else:
            record.update(stage=stage, assessment=assessment)
        save_workspace(user, current)
        return record

    @app.get("/api/compare")
    def compare(user: User = Depends(current_user)):
        current = workspace(user)
        jd = next((item for item in current.jds if item.id == current.selected_jd_id), None)
        can_compare = jd is not None and jd.reviewed_at is not None and bool(jd.required or jd.preferred)
        return {"jd": jd_response(jd) if jd else None, "results": [match_response(item) for item in rank(jd, current.candidates)] if can_compare else []}

    @app.get("/api/candidates/{candidate_id}/analysis")
    def candidate_analysis(candidate_id: str, user: User = Depends(current_user)):
        current = workspace(user)
        candidate = get_candidate(current, candidate_id)
        jd = active_jd(current)
        if jd.reviewed_at is None or not (jd.required or jd.preferred):
            raise HTTPException(status_code=409, detail="Review this job description's skills before comparing candidates.")
        match = next(item for item in rank(jd, current.candidates) if item.candidate_id == candidate_id)
        return {"candidate": candidate_response(candidate, include_evidence=True), "jd": jd_response(jd, include_evidence=True), "match": match_response(match), "summary": generate_summary(jd, candidate, match), "questions": generate_questions(jd, candidate, match)}

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
            return FileResponse(frontend / "index.html", headers={"Cache-Control": "no-store"})

    return app


app = create_app()
