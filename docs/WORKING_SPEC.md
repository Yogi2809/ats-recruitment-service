# RoleTrace — working product specification

**Audience:** recruiter demo reviewer and implementation interviewer. **Version:** 7 November 2026. Use [the live app](https://roletrace.vercel.app) with synthetic data. The root [README](../README.md) has setup and a five-minute walkthrough; the [HLD](HLD.md) explains components and decisions.

## What a recruiter can do

| Assignment need | RoleTrace behavior | What the reviewer sees |
| --- | --- | --- |
| Add JDs and CVs | Separate paste and upload controls for each; PDF, DOCX, TXT; multiple CV files can be selected. | Saved documents in the private workspace and extracted JD skill lists. |
| Match and rank | Compare all saved CVs with the selected JD. | Ranked cards, alignment donut, required/preferred coverage bars, labels, found/gap skill chips. |
| Inspect why | Open **View evidence and prepare**. | Skill table with CV excerpt and source location for each found skill; “No evidence found” for gaps. |
| Prepare interview | Open a candidate review. | Short grounded summary and role-specific questions derived from required/preferred skills. |
| Track progress | Choose a candidate stage and optionally write an assessment note. | Saved stage in that user's workspace; chat can report it with a recruitment-record source. |
| Draft mail | Choose candidate and invitation or assessment instructions. | Editable saved draft with copy and delete actions; no mail is sent. |
| Ask questions | Open the floating chat icon on any signed-in screen. | Answers about loaded candidates, skills, ranking, status, and interview preparation. Sources can be expanded. |

## Screen flow and expected states

1. **Login/create account.** Email and password are required. Registration asks for password confirmation and at least 12 characters. A mismatched confirmation is shown in the form. A duplicate email cannot create another account; a wrong login returns “Email or password is incorrect.” **Keep me signed in** controls the session lifetime. Successful login opens the user's workspace.
2. **Overview.** A new account shows “No role selected,” zero candidates, no top alignment, and a prompt to add documents. It does not show Maya, Arjun, Neha, or any other sample person until a user supplies files. The overview later shows the selected role, candidate count, top score, and ranked candidate links.
3. **Documents.** JD and CV have independent **Paste text** and **Upload file(s)** choices. Paste requires a title/name and text and is saved with an Add button. Choosing a PDF, DOCX, or TXT file starts its upload immediately; a success notice and the new document count confirm completion. A document is limited to 4 MiB. If saving fails, pasted text remains in the form and an error is shown. The most recently added JD becomes active. After adding a JD, the **Review skills** panel opens. Choose a role if the file contains several, inspect each source quote, adjust categories or terms, and save the reviewed list. **Reanalyse skills** offers a fresh preview for an existing JD without replacing saved edits until approved. Candidate CVs can be removed. Older accounts with legacy bundled samples see **Remove bundled samples**, which removes only those known bundled records and their related drafts; user-added documents remain.
4. **Compare candidates.** Results appear after the active JD has a saved review with at least one required or preferred skill. An unreviewed JD or a reviewed list without scored skills shows guidance back to Documents. Results are recalculated for the active JD, sorted by alignment by default or by name on request. Each card displays the percentage donut, category bars, match label, matched required skills, and required skills with no CV evidence. With no active JD or CV, an empty state directs the user to Documents. The displayed percentage is RoleTrace's own ATS-style comparison, not an external ATS result or hiring recommendation.

**Document management and sharing:** Separate searches filter JDs and candidates independently. A recruiter can assign a JD department, maintain candidate tags, filter by tag, view extracted source text, delete their own documents, and select multiple JD or CV files for upload. Compare provides a JD selector and candidate checkboxes; the candidate selection stays in place when returning from a candidate review. The dashboard's document counts open the relevant lists. From Documents, **Share** publishes an explicit snapshot to the authenticated users' read-only **Shared library**. The library supports search, view, download where available, and importing a separate copy. Unsharing or deleting the original removes its listing; imported copies remain independent. Legacy uploads may lack original files; legacy pasted text is labelled as extracted when reconstructed.
5. **Candidate review.** **View evidence and prepare** opens the selected candidate against the active JD. The page shows the score breakdown, each required/preferred skill, supporting excerpt/location or gap, summary, and up to seven interview questions. **Draft email** opens the drafts screen. A separate status panel lets the recruiter save one of the listed stages and an optional assessment note (500-character maximum). The floating chat icon opens chat with this candidate already selected. A missing status is displayed as **No status recorded**.
6. **Chat.** The floating icon opens a panel, not a new page. The recruiter may select **All candidates** or one candidate, type a question, use a suggested prompt, inspect expandable sources, and close the panel. With no JD/CV, chat explains what to add. Without an LLM key, supported questions use deterministic, evidence-based answers. Unknown facts, such as an unrecorded recruitment stage or unverified certification, are stated as unknown. The optional server-side Groq integration can make supported answers more flexible, but it is not required for the demo and was not used in the production QA run.
7. **Email drafts.** Choose a candidate, draft type, date/deadline, time, and link/location. The app creates an editable invitation or assessment message. Save edits to persist them; Copy text puts the current editor text on the clipboard; Delete draft removes it. Placeholders appear if date/time/link were omitted. A recruiter must review and send the text using their own email service.
8. **Theme, mobile, logout.** The top bar toggles light/dark mode; the preference stays in that browser's local storage. A narrow screen uses a menu to open the sidebar. **Log out** removes the session cookie and returns to login. The account's workspace stays in Postgres and reappears after login.

## Example: one complete review

Suppose a JD says “Required: Python, SQL, Airflow. Preferred: AWS.” A synthetic CV says “Built Python and SQL pipelines with Airflow” and says nothing about AWS. The skill table shows Python, SQL, and Airflow as **Found**, each with a source line, and AWS as **No evidence found**. The score also includes wording similarity; it is not simply 3/4. The summary describes the mentions and gap. A question asks about the candidate's Airflow contribution and another asks about AWS experience. If the recruiter records **Recruiter screen** with “Data exercise pending,” chat can answer “What assessment is this candidate assigned?” from that saved record. Before saving, chat says the status is not recorded.

## Matching rules and data interpretation

- Requirements are suggested from role sections, local requirement language, a shared term catalog, and short skill phrases. Automatic rows have source quotes and locations. The recruiter must review and save the list before scores appear. Unknown terms may still be missed; a custom skill entered by the recruiter is checked as a literal phrase.
- Skill coverage counts JD skills with a CV mention. A limited negation rule skips some explicit “no/without/lack” mentions. The wording component uses TF-IDF cosine similarity of the extracted JD and CV text.
- Weights are 70% required, 20% preferred, and 10% wording when both categories exist. An empty skill category's weight is redistributed among the remaining factors. Score and category percentages are rounded to integers.
- **Strong evidence match:** at least 80%. **Partial evidence match:** 55–79%. **Needs review:** below 55%. These are display bands, not verified hiring outcomes.
- Excerpts in ordinary API responses are capped for usability; the full text remains in the user's workspace database. A gap means no matching mention was found, not proof that the person has no experience.

## API contract (principal routes)

All `/api` routes below except registration, login, and logout require a valid session cookie. JSON is used except for multipart uploads.

| Route | Input and result |
| --- | --- |
| `POST /api/auth/register`, `POST /api/auth/login` | Email, password, `keep_signed_in`; returns user ID/email and sets cookie. |
| `GET /api/auth/me`, `POST /api/auth/logout` | Identify current account; delete session cookie. |
| `GET /api/workspace` | Current user's compact JDs/CVs, selected JD ID, recruitment records, drafts. |
| `POST /api/jds/paste`, `POST /api/jds/upload` | Save one JD; upload field is `file`. |
| `POST /api/jds/{id}/skills/preview`, `PUT /api/jds/{id}/skills` | Preview sourced suggestions for a role; save the recruiter-reviewed requirements. |
| `GET /api/jds/{id}`, `GET /api/candidates/{id}` | View complete extracted text for a document in the authenticated user's workspace. |
| `PATCH /api/jds/{id}/metadata`, `PATCH /api/candidates/{id}/metadata` | Set a department or candidate tags. |
| `GET /api/library`, `POST /api/library/share/{kind}/{id}` | List opt-in shared documents or publish the owner's JD or candidate snapshot. |
| `GET /api/library/{id}`, `GET /api/library/{id}/download` | View an authenticated shared snapshot or download its stored file when available. |
| `POST /api/library/{id}/copy`, `DELETE /api/library/{id}` | Import an independent copy, or unshare a document owned by the requester. |
| `POST /api/jds/{id}/select`, `PATCH /api/jds/{id}` | Select JD; edit title and required/preferred lists. |
| `POST /api/candidates/paste`, `POST /api/candidates/upload` | Save one candidate; upload field is `file`. The browser loops over selected CV files. |
| `DELETE /api/candidates/{id}` | Remove the candidate and their recruitment record. Existing draft snapshots remain until individually deleted. |
| `PATCH /api/candidates/{id}/recruitment` | Save nonblank `stage` (up to 80 characters) and optional `assessment` (up to 500). |
| `GET /api/compare`, `GET /api/candidates/{id}/analysis` | Ranked comparison; one candidate's evidence, summary, and questions. |
| `POST /api/chat` | `question` and optional `candidate_id`; returns answer text and source excerpts. |
| `POST /api/drafts/generate`, `PATCH /api/drafts/{id}`, `DELETE /api/drafts/{id}` | Create, edit, and remove saved drafts. |
| `DELETE /api/workspace/sample-data` | Remove only deterministic legacy bundled examples. |
| `GET /health` | Public health response `{ "status": "ok" }`. |

Common responses: `401` for no valid session, `404` for a missing or other-account resource, `409` when a feature needs an active JD or registration hits a duplicate email, and `422` for invalid input or unsupported/unreadable/oversized documents. A direct route call cannot fetch another user's workspace by supplying an ID; the server takes the account ID from the signed session.

## Setup, operation, and limits

The shareable deployment uses Vercel for the UI/API and Neon Postgres for persistence. Its required private environment variables are `DATABASE_URL`, `SECRET_KEY`, and `APP_ENV=production`; `GROQ_API_KEY` is optional. Local setup uses SQLite by default. The optional synthetic files in `sample_data/` are never automatically loaded for a new account. See the [README](../README.md) for exact commands and [QA_REPORT.md](QA_REPORT.md) for what was verified.

This is an interview prototype. It has no OCR for scanned PDFs, email delivery, ATS integration, password reset, email verification, rate limiting, audit log, or measured fairness validation. Multiuser separation was tested for **different accounts**; concurrent edits from two devices signed into the **same account** may overwrite one another because a workspace is saved as one JSON object. The app should be demonstrated with synthetic data only.
