# Recruiter Assistant: Design Specification

Date: 6 November 2026
Status: approved with subsequent user refinements on 6 November 2026

## Goal and demo story

Build a shareable Python prototype for a recruiter to inspect synthetic CVs and job descriptions, compare candidates, ask open-ended recruitment questions, and draft interview materials. A reviewer creates an email/password account and signs in to use the app; no reviewer API key is needed. The owner configures one optional server-side free-tier LLM key for flexible conversation. All five assignment requirements must remain usable if that key is absent or quota is exhausted.

Primary demonstration: select a sample JD, inspect a ranked shortlist with supporting excerpts, ask why two candidates differ, generate a summary and interview questions, then draft an invitation or assessment email. The outputs are assistance for a human recruiter, not an automated hiring decision.

## Scope

The app will include at least two synthetic JDs, six synthetic CVs with deliberately varied skill coverage, and a small synthetic recruitment-status dataset. It will accept text-based PDF, DOCX, and TXT uploads for JDs and CVs. It will not provide OCR for scanned PDFs, send emails, connect to an ATS, or persist uploads across sessions. The UI will explain extraction failures and empty documents.

## Architecture and boundaries

One FastAPI service and React frontend call focused Python modules:

1. **Document ingestion** accepts either uploads or pasted text in separate JD and CV input controls. It extracts text and source locations (PDF page, DOCX paragraph, TXT line, or pasted-text line), validates file type and size, and creates normalized evidence chunks. It treats supplied text as data, never as instructions.
2. **Authentication and recruitment store** persists registered email accounts and password hashes in a database, supports login, optional keep-signed-in duration, and logout, and protects application routes. Each signed-in user's JDs, candidates, and synthetic recruitment records are isolated in server memory. Sample data loads on first launch. Uploaded documents are not written to disk and disappear after service restart or session expiry.
3. **Matcher** identifies canonical skills from a documented alias catalog, records the exact supporting excerpt for each hit, and computes reproducible rankings. It does not infer that an unmentioned skill is absent in reality.
4. **Retrieval and answer service** resolves candidate/JD names, retrieves relevant chunks and structured records, and creates an answer with source labels. With a configured Groq key, an LLM phrases the answer and handles varied recruiter questions. Without one, a limited rule-based answer service covers the included demo questions and gives a clear unsupported-question response.
5. **Draft service** produces evidence-based summaries, role-specific interview questions, invitation emails, and assessment instructions. LLM wording is used when available; deterministic templates provide the fallback. Emails are displayed as editable drafts and never sent.
6. **React UI and FastAPI service** present the workspace and expose document, ranking, draft, and chat endpoints. FastAPI also serves the built frontend from the same public service. The UI follows `docs/stitch-ui-brief.md`, including light/dark themes, visual comparisons, and a floating chat drawer.

No vector database or separate backend is needed for the small, session-local dataset. The modules expose plain Python functions so scoring and retrieval can be tested without the UI or API.

## Ranking method

The selected JD is parsed into required and preferred skill lists, shown to the recruiter for review and correction. Skills are normalized through an alias table (for example, `Postgres` to `PostgreSQL`). Required-skill coverage contributes 70% of the displayed score, preferred-skill coverage 20%, and lexical JD/CV similarity 10%. Similarity uses word-level TF-IDF cosine similarity, calculated across the active JD and candidate documents. Empty skill lists redistribute their weight across the remaining nonempty components. Ties sort by candidate ID for stable results.

The result card shows an **ATS-style JD alignment score** as a percentage, not a claim about any external ATS. Bands are Strong alignment (80–100), Possible alignment (60–79), and Limited evidence (0–59). The UI includes an overall donut, a side-by-side comparison of score components, JD terminology found/not found, and a table of matched requirements and requirements for which the CV provides no evidence, each linked to supporting excerpts. The score means match to the supplied JD and CV text. It is not a probability of job success. Experience is summarized only when an explicit passage supports it; experience is not silently estimated from dates.

## Chat and grounding

The user can ask open-ended recruitment questions. The answer service uses the current JD, candidate records, ranking results, recruitment-status data, and retrieved document excerpts. Candidate-specific factual claims must carry source labels that the UI can expand to exact excerpts. The LLM receives only relevant excerpts and structured facts, not unrestricted access to all files. It must treat document text as untrusted content and ignore instructions embedded in CVs or JDs.

The LLM may provide general recruiter advice, clearly marked as general advice. It may suggest interview follow-ups based on gaps, but cannot state that an unmentioned skill is definitely absent. If the supplied data cannot establish a candidate-specific fact, the response states the uncertainty. The app validates returned source IDs against supplied evidence before display and rejects invalid citations. This does not guarantee every generated sentence is correct; the UI keeps evidence visible for human review.

Out-of-domain requests receive a short redirect to recruitment tasks. Ranking and numeric counts are computed by Python, not by the LLM. For API timeout, error, or quota exhaustion, the UI reports that flexible AI chat is temporarily unavailable and uses the no-key fallback for supported questions and drafts.

## Interface and interaction

The product is named **RoleTrace**. The default post-login screen has sample data loaded. The workspace has separate JD and CV inputs, each with upload and paste tabs. The top identifies the active JD and candidate count. A ranked table or cards show fit, skills, gaps, and evidence. Selecting a candidate reveals comparison charts, a skills/evidence table, summary, interview questions, and draft email actions. A single persistent bottom-right chat launcher opens a responsive chat drawer; there are no duplicate Ask Assistant buttons. Every generated text area can be copied; email drafts can be edited before copying. The login and account-creation pages are minimal forms. The UI uses the Paper & Ember light/dark palette in `docs/stitch-reference/roletrace-DESIGN.md`, plain and concise copy, and a responsive mobile layout. The implementation is an original design informed by the user's requirements, not a copy of the Stitch screens.

The UI marks synthetic sample data, explains that uploaded files are session-local, and warns users to avoid real candidate information in the public demo. Relevant excerpts may be transmitted to Groq when AI chat or drafting is used; the UI says so. The app does not request a reviewer's API key. The owner configures `GROQ_API_KEY` as a Render environment variable and can set the model through configuration. The key never appears in UI or repository files. The extracted Stitch design in `docs/stitch-reference/` is a visual reference; unsupported claims and static values identified in its README are not copied into the working app.

## Tests and acceptance criteria

Unit tests cover document extraction from minimal PDF/DOCX/TXT fixtures, skill aliases, ranking order and score components, retrieval source IDs, unsupported claims, and fallback behavior. Tests mock the LLM; live API access is not required for the test suite. A small manual smoke test verifies the full five-step demo locally and on the deployed URL.

The prototype is accepted when a reviewer can: (1) use sample data immediately; (2) upload supported CVs and a JD; (3) inspect stable ranking with skill evidence and gaps; (4) generate grounded summaries and role-specific questions; (5) create both requested email types; and (6) ask varied recruitment questions and see either a supported answer with evidence or a clear uncertainty response. The README explains setup, key configuration, design, limitations, and a short demo script.

## Deployment

Publish source and synthetic data to a public GitHub repository and deploy one FastAPI web service on Render, serving both the API and compiled React assets from an `onrender.com` URL. Configure the Groq key only as a Render environment variable. Use local SQLite for development and a persistent managed Postgres database in deployment so user accounts survive web-service restarts; uploaded documents remain session-local. The app must function without the Groq secret for reviewers and local runs. Before submission, visit the deployed link to wake it, verify the demo flow, and include both app and repository links in the submission. Render's free service spins down after idle time and has ephemeral storage; Groq free-tier availability is quota limited. The README supplies local-run instructions and the no-key fallback.

