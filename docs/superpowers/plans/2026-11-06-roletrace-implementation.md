# RoleTrace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a shareable recruiter web app with account access, evidence-based JD/CV comparison, grounded chat, and recruitment drafts.

**Architecture:** FastAPI serves JSON endpoints and the compiled React application. Focused Python modules extract documents, detect skills, rank candidates, retrieve evidence, and create drafts; an optional Groq client phrases grounded answers. A persistent SQL database stores accounts; uploaded documents and active comparisons are per-user in memory.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Argon2, pypdf, python-docx, scikit-learn, pytest, React, TypeScript, Vite, CSS, Recharts, Docker, Render.

**Spec:** `docs/superpowers/specs/2026-11-06-recruiter-assistant-design.md`

## Global Constraints

- Product name: RoleTrace. UI copy is short and functional; Paper & Ember colors come from `docs/stitch-reference/roletrace-DESIGN.md`.
- PDF/DOCX/TXT uploads and pasted JD/CV text. Scanned PDF without extracted text returns a useful error.
- Score: 70% required-skill coverage, 20% preferred-skill coverage, 10% JD/CV TF-IDF similarity; empty categories redistribute weight.
- Candidate facts cite source excerpts. No evidence found is not a claim of absent ability.
- Groq is optional; all assignment requirements retain a no-key path. Never store a key in the repository.
- Email drafts are editable and never sent. Synthetic data only for public demo.
- Registration/login/logout protect workspace APIs. Account records persist in SQLite locally and Postgres on Render; uploads are session-local.

## File map

- `backend/app/main.py`: FastAPI routes, auth guard, static frontend serving.
- `backend/app/auth.py`: account persistence, password hashing, signed session cookies.
- `backend/app/models.py`: typed JD, candidate, evidence, match, and draft data.
- `backend/app/documents.py`: PDF/DOCX/TXT/paste extraction and evidence locations.
- `backend/app/matching.py`: skill aliases, score and evidence breakdown.
- `backend/app/assistant.py`: retrieval, fallback chat, optional Groq calls, drafts.
- `backend/app/sample_data.py`: synthetic JDs, CVs, recruitment records.
- `frontend/src/App.tsx`: routing and global app state.
- `frontend/src/components/`: minimal auth, workspace, ranking, candidate detail, drafts, chatbot views.
- `frontend/src/styles.css`: Paper & Ember light/dark responsive system.
- `tests/`: meaningful backend and API tests.
- `Dockerfile`, `requirements.txt`, `frontend/package.json`, `README.md`: reproducible build, deployment, and demo.

---

### Task 1: Accounts and protected API

**Files:** Create `backend/app/auth.py`, `backend/app/main.py`, `tests/test_auth.py`, `requirements.txt`.

**Interfaces:** `register(email: str, password: str) -> User`; `authenticate(email: str, password: str) -> User | None`; `get_current_user(request: Request) -> User`; routes `/api/auth/register`, `/api/auth/login`, `/api/auth/me`, `/api/auth/logout`.

- [ ] Write failing tests for registration, duplicate account, wrong password, protected route, and logout. Example assertion:
  ```python
  assert client.post('/api/auth/login', json={'email':'unknown@example.test','password':'wrong'}).status_code == 401
  ```
- [ ] Run `python3 -m pytest tests/test_auth.py -q` and confirm failure before implementation.
- [ ] Implement SQLAlchemy user table, Argon2 hash, signed HttpOnly SameSite cookie, optional seven-day session, generic invalid-credentials response, and auth guard.
- [ ] Run targeted tests and commit account/API foundation.

### Task 2: Documents, sample data, and ranking

**Files:** Create `backend/app/models.py`, `backend/app/documents.py`, `backend/app/matching.py`, `backend/app/sample_data.py`, `tests/test_documents.py`, `tests/test_matching.py`.

**Interfaces:** `extract_document(filename: str, data: bytes) -> list[Evidence]`; `extract_paste(text: str) -> list[Evidence]`; `rank(jd: JobDescription, candidates: list[Candidate]) -> list[MatchResult]`.

- [ ] Write failing tests for PDF/DOCX/TXT/paste locations, empty scan error, skill aliases, required/preferred coverage, score formula, stable tie ordering, and matched excerpts. Example:
  ```python
  assert rank(jd, [python_candidate, unrelated_candidate])[0].candidate_id == 'python_candidate'
  ```
- [ ] Run `python3 -m pytest tests/test_documents.py tests/test_matching.py -q` and confirm failures.
- [ ] Implement text extraction, six synthetic CVs, two synthetic JDs, recruitment records, alias detection, TF-IDF similarity, and evidence-linked score breakdown.
- [ ] Run targeted tests and commit the analysis core.

### Task 3: Workspace, drafts, and grounded chat API

**Files:** Modify `backend/app/main.py`; create `backend/app/assistant.py`, `tests/test_api.py`, `tests/test_assistant.py`.

**Interfaces:** `/api/workspace`, `/api/jds`, `/api/candidates`, `/api/compare`, `/api/drafts`, `/api/chat`; `answer(question: str, context: Workspace, groq_client=None) -> ChatAnswer`.

- [ ] Write failing tests for per-user isolation, upload and paste, comparison JSON, source IDs, unsupported facts, no-key answer and draft, invalid citation rejection, and Groq error fallback. Example:
  ```python
  assert 'not established' in answer('Does Maya have a certification?', sample_workspace).text.lower()
  ```
- [ ] Run `python3 -m pytest tests/test_api.py tests/test_assistant.py -q` and confirm failures.
- [ ] Implement per-user workspace, REST routes, retrieval, response citations, summary/question/email templates, and optional Groq request with timeout and bounded context.
- [ ] Run targeted tests and commit service behavior.

### Task 4: Responsive React interface

**Files:** Create `frontend/package.json`, `frontend/index.html`, `frontend/src/App.tsx`, `frontend/src/components/*.tsx`, `frontend/src/styles.css`.

**Interfaces:** React calls the Task 1–3 `/api` routes using credentialed fetch; all signed-in screens share active JD/candidate and theme state.

- [ ] Create frontend interaction checks for login/register/logout, upload/paste tabs, compare navigation, candidate detail, draft editing, and floating chat open/close. Use a small browser smoke test for the main journey rather than tests that duplicate markup.
- [ ] Build minimal login/create-account screens, Overview, Jobs & CVs, Compare, Candidate Detail, Drafts, and persistent chat drawer with no duplicate Ask Assistant button.
- [ ] Apply Paper & Ember light/dark CSS, responsive layout, charts, evidence table, loading/errors, and keyboard labels. Ensure the launcher does not cover page actions.
- [ ] Run `npm run build` and the interaction smoke test; commit the frontend.

### Task 5: Packaging, verification, and deployment preparation

**Files:** Create `Dockerfile`, `.dockerignore`, `.gitignore`, `README.md`, `render.yaml`; modify `backend/app/main.py` for static assets.

**Interfaces:** `docker build` produces one image serving both `/api` and the React app on `$PORT`; `/health` reports readiness without exposing secrets.

- [ ] Add a test that the built frontend and `/health` are served, then implement Docker multi-stage build and static-file fallback.
- [ ] Run all backend tests, frontend build, and a local full-flow smoke test: account → sample JD/CVs → comparison → evidence → chat → questions → email draft → logout.
- [ ] Write setup, Groq key configuration, deployment, demo script, score formula, privacy limitations, and no-key behavior in README.
- [ ] Check no secrets or real candidate data are tracked; commit packaging.
- [ ] Publish to GitHub and deploy to Render only when connected accounts or user-provided deployment credentials are available; verify the public URL and document any external-account blocker precisely.

## Self-review

- Spec coverage: uploads/paste, rank/chart evidence, summary/questions, both email types, chat, accounts, light/dark UI, synthetic samples, and Render packaging all map to tasks above.
- Type/API naming: frontend consumes `/api` route names listed in Tasks 1 and 3; matching and assistant signatures are stable.
- No secret is required for local tests or the fallback demo.
