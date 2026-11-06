# RoleTrace

A recruiter workspace for reviewing synthetic CVs against job descriptions. It extracts text from PDF, DOCX, and TXT files or pasted text; ranks candidates with an explainable **ATS-style JD alignment** percentage; shows the matching lines and gaps; prepares interview questions and email drafts; and answers questions through a floating recruiter chat.

The design uses a warm Paper & Ember palette in light and dark modes. The UI is responsive and requires an email/password account. All included people and recruitment records are synthetic.

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

Open `http://localhost:8000`, create an account with a password of at least 12 characters, and use the preloaded sample role and candidates. Local accounts are stored in `roletrace.db`; your added documents and drafts remain in server memory and reset when the server restarts.

For frontend development, run `npm run dev` in `frontend/` while the Python server runs on port 8000. Vite proxies `/api` to Python.

## Five-minute demo

1. Create an account. The workspace opens with two synthetic JDs and six synthetic CVs.
2. Open **Documents**. Select **Senior Data Engineer**, inspect its required/preferred skills, then paste or upload a JD/CV. The `sample_data/` folder has uploadable TXT examples.
3. Open **Compare candidates**. Review the ranked cards, donut percentage, coverage bars, and the plain-language matching label.
4. Click **View evidence and prepare** on Maya Shah. Inspect the skill table, source lines, summary, and role-specific interview questions.
5. Click the floating **Ask RoleTrace** button. Try “Why is Maya a match?”, “Who has Airflow?”, and “What should I ask Maya?” Open the source excerpts beneath each answer.
6. Open **Email drafts**. Generate an interview invitation or assessment instructions, edit the text, save it, and copy it. The app does not send email.
7. Switch light/dark mode in the top bar, then log out in the sidebar.

## How matching works

For each JD, the app detects a small catalog of skill names and aliases. The recruiter can edit the required and preferred skill lists before comparing. Each CV is checked for mentions of those skills, and the matching text is kept as evidence. The wording similarity is TF-IDF cosine similarity between the JD and CV text.

The score is `70% × required coverage + 20% × preferred coverage + 10% × wording similarity`. If a JD has no required or preferred skills, its missing category's weight is redistributed among the remaining components. This is **RoleTrace's own comparison**, not an external ATS score. A skill absent from a CV is labeled **No evidence found**; it does not establish that the candidate lacks the skill. The score helps a recruiter decide what to inspect and ask, not whom to hire.

## Chat and optional LLM

No API key is needed for the full demo. Without a key, chat answers supported candidate, skill, stage, ranking, and interview-question queries using deterministic code and cited sample data. It explicitly says when a fact, such as certification or availability, is not established.

For more flexible, natural recruiter questions, set `GROQ_API_KEY` as a **server-side environment variable**. The default model is `openai/gpt-oss-20b`, configurable with `GROQ_MODEL`. Create a key in the [Groq console](https://console.groq.com/keys) and check its current free-plan limits. Never place the key in frontend code, a public repository, or a screenshot. If Groq is unavailable or returns unusable citations, RoleTrace falls back to its no-key answer. CV excerpts are sent to Groq only when the key is configured; use synthetic data for this demo.

## Deploy a shareable URL

The repository includes a multi-stage `Dockerfile` and a Render Blueprint in `render.yaml`. Push the repository to your own GitHub account, then in Render choose **New → Blueprint** and connect the repository. Render will build one web service for the UI/API and a Postgres database for account records. Open the generated `onrender.com` URL, create a reviewer account, and run the demo steps above. You can optionally add `GROQ_API_KEY` in the Render web service's environment settings.

The Blueprint sets `SECRET_KEY` automatically and uses secure session cookies in production. Free Render web services may sleep when idle, so the first request can take longer. Render's free Postgres databases currently expire after 30 days; deploy near the interview date or choose another database plan for a longer-lived link. Uploaded documents and drafts are intentionally kept in memory for this prototype and reset on redeploy, restart, or sleep. Accounts remain in Postgres while that database exists. Use synthetic data only.

## Tests

```bash
python -m pytest -q
cd frontend && npm test && npm run build
```

## Project map

- `backend/app/main.py`: API routes, account protection, and compiled frontend serving
- `backend/app/auth.py`: account database, Argon2 passwords, signed cookies
- `backend/app/documents.py`: PDF/DOCX/TXT extraction with page/line locations
- `backend/app/matching.py`: aliases, score, ranking, and evidence
- `backend/app/assistant.py`: summaries, interview questions, drafts, and chat
- `backend/app/sample_data.py`: synthetic demo data
- `frontend/src/App.tsx`: screen flows and API interactions
- `frontend/src/styles.css`: responsive light/dark design system
- `sample_data/`: uploadable synthetic TXT examples
- `tests/`: backend and API checks

## Prototype limits

This is an interview prototype. It does not perform OCR on scanned PDFs, verify credentials, send emails, integrate with an ATS, or make hiring decisions. The skill catalog is deliberately small and can miss synonyms; recruiters can edit JD skills. Account records persist, while user documents and drafts are stored in a single server process and are not suitable for long-term or multi-instance storage. A production system would add persistent document storage, audit controls, deeper evaluation for bias and accuracy, and stronger account abuse protection.
