# RoleTrace

**Live demo:** [roletrace.vercel.app](https://roletrace.vercel.app) — create an account, then add your own synthetic test documents. New accounts start with an empty workspace. No API key is required.

A recruiter workspace for reviewing synthetic CVs against job descriptions. It extracts text from PDF, DOCX, and TXT files or pasted text; ranks candidates with an explainable **ATS-style JD alignment** percentage; shows the matching lines and gaps; prepares interview questions and email drafts; records candidate recruitment stages; and answers questions through a floating recruiter chat.

Each document can contain up to 4 MB of readable text or file data. The deployed limit leaves room beneath [Vercel's 4.5 MB request-body cap](https://vercel.com/docs/functions/limitations). The database keeps the extracted text; ordinary API responses return compact excerpts so comparisons remain usable as documents accumulate.

The design uses a warm Paper & Ember palette in light and dark modes. The UI is responsive and requires an email/password account. All included people and recruitment records are synthetic.

For the interview walkthrough, see the [high-level design](docs/HLD.md), [complete working specification](docs/WORKING_SPEC.md), and [QA report](docs/QA_REPORT.md).

## Quick start

Requires Python 3.12+ and Node.js 22+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn backend.app.main:app --reload --port 8000
```

Open `http://localhost:8000`, create an account with a password of at least 12 characters, and add a JD and CVs. The `sample_data/` directory contains optional synthetic files to upload or paste. Local accounts, added documents, and drafts are stored in `roletrace.db` and survive a server restart.

For frontend development, run `npm run dev` in `frontend/` while the Python server runs on port 8000. Vite proxies `/api` to Python.

## Five-minute demo

1. Create an account. The workspace starts empty.
2. Open **Documents**. Upload `sample_data/senior_data_engineer_jd.txt` and one or more CVs from `sample_data/`, or paste synthetic text into the separate JD and CV forms. Review the extracted required/preferred skills.
3. Open **Compare candidates**. Review the ranked cards, donut percentage, coverage bars, and the plain-language matching label.
4. Click **View evidence and prepare** on Maya Shah. Inspect the skill table, source lines, summary, and role-specific interview questions. Save a recruitment stage and an optional assessment note.
5. Click the floating chat icon in the bottom right. Try “Why is Maya a match?”, “Who has Airflow?”, “What should I ask Maya?”, and “What stage is Maya at?” Open the source excerpts beneath each answer.
6. Open **Email drafts**. Generate an interview invitation or assessment instructions, edit the text, save it, and copy it. The app does not send email.
7. Switch light/dark mode in the top bar, then log out in the sidebar.

Accounts created before the empty-workspace update may still contain the original bundled examples. In **Documents**, use **Remove bundled samples** to remove those examples and their related drafts while keeping your own uploads.

## How matching works

For each JD, the app detects a small catalog of skill names and aliases. The recruiter can edit the required and preferred skill lists before comparing. Each CV is checked for mentions of those skills, and the matching text is kept as evidence. The wording similarity is TF-IDF cosine similarity between the JD and CV text.

The score is `70% × required coverage + 20% × preferred coverage + 10% × wording similarity`. If a JD has no required or preferred skills, its missing category's weight is redistributed among the remaining components. This is **RoleTrace's own comparison**, not an external ATS score. A skill absent from a CV is labeled **No evidence found**; it does not establish that the candidate lacks the skill. The score helps a recruiter decide what to inspect and ask, not whom to hire.

## Chat and optional LLM

No API key is needed for the full demo. Without a key, chat answers supported candidate, skill, stage, ranking, and interview-question queries using deterministic code and cited workspace data. It explicitly says when a fact, such as certification or availability, is not established.

For more flexible, natural recruiter questions, set `GROQ_API_KEY` as a **server-side environment variable**. The default model is `openai/gpt-oss-20b`, configurable with `GROQ_MODEL`. Create a key in the [Groq console](https://console.groq.com/keys) and check its current free-plan limits. Never place the key in frontend code, a public repository, or a screenshot. If Groq is unavailable or returns unusable citations, RoleTrace falls back to its no-key answer. CV excerpts are sent to Groq only when the key is configured; use synthetic data for this demo.

## Deploy a shareable URL

The no-card deployment uses **Vercel Hobby** for the FastAPI web app and **Neon Free** for Postgres. The root `app.py` is Vercel's Python entrypoint, and the compiled React files in `frontend/dist/` are included in the repository. Import this repository at `vercel.com/new`, keep the project root as the repository root, and set these server-side environment variables:

- `DATABASE_URL`: the Neon project's pooled Postgres connection string.
- `SECRET_KEY`: a long, randomly generated value for signed login sessions.
- `APP_ENV`: `production`.
- `GROQ_API_KEY` (optional): enables more flexible recruiter chat.

Deploy on the free Hobby plan and open the generated `vercel.app` link. The first request can take longer while Python dependencies load. Vercel Functions can run on different instances, so RoleTrace saves account and workspace data in Neon instead of relying on process memory. Use synthetic data only; never put the database URL or API key in GitHub or frontend code.

The Dockerfile and `render.yaml` are also included for container hosting. Render currently requires a card on this account even for a free service, so Vercel is the default no-card route for this submission.

## Tests

```bash
python -m pytest -q
cd frontend && npm test && npm run build
```

For a live deployment check, run `python tests/live_smoke.py https://roletrace.vercel.app`. This creates two synthetic test accounts and documents in the target database; it uses no real candidate information.

## Project map

- `backend/app/main.py`: API routes, account protection, and compiled frontend serving
- `backend/app/auth.py`: account database, Argon2 passwords, signed cookies
- `backend/app/documents.py`: PDF/DOCX/TXT extraction with page/line locations
- `backend/app/matching.py`: aliases, score, ranking, and evidence
- `backend/app/serializers.py`: compact, relevant API evidence excerpts
- `backend/app/assistant.py`: summaries, interview questions, drafts, and chat
- `backend/app/sample_data.py`: synthetic demo data
- `frontend/src/App.tsx`: screen flows and API interactions
- `frontend/src/styles.css`: responsive light/dark design system
- `sample_data/`: uploadable synthetic TXT examples
- `tests/`: backend and API checks

## Prototype limits

This is an interview prototype. It does not perform OCR on scanned PDFs, verify credentials, send emails, integrate with an ATS, or make hiring decisions. The skill catalog is deliberately small and can miss synonyms; recruiters can edit JD skills. Workspace data is stored in Postgres as JSON for the demo; a production system would add dedicated document storage, audit controls, deeper evaluation for bias and accuracy, and stronger account abuse protection.
