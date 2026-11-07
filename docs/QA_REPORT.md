# RoleTrace — quality assurance report

**Date:** 6 November 2026 (IST). **Target:** [https://roletrace.vercel.app](https://roletrace.vercel.app). **Data:** synthetic accounts, JDs, and CVs only. **Result:** the tested release passed the automated live flow and the manual interface checks listed below. This is a prototype verification, not a security or accessibility certification.

## Method

We used Python API tests, React component tests, a production frontend build, a live HTTP smoke test, and browser interaction. The [live test script](../tests/live_smoke.py) makes two random synthetic accounts, uses separate cookie jars like two independent clients, and exercises the public URL against its Neon-backed database. It does not use the recruiter's real account. Browser checks used a separate synthetic account. Source changes are linked in the [HLD](HLD.md) and [working spec](WORKING_SPEC.md).

To reproduce locally:

```bash
python -m pytest -q
cd frontend
npm test
npm run build
```

To repeat against a deployment (creates two synthetic accounts and saved test documents):

```bash
python tests/live_smoke.py https://roletrace.vercel.app
```

## Automated results

| Gate | Result | What it covers |
| --- | --- | --- |
| Backend/API | 32 tests passed | Auth, empty workspace, upload/parse, ranking, grounding, stage CRUD, tenant checks, static serving, edge inputs. |
| React interface | 9 tests passed | Registration, empty screens, file selection upload, key actions, candidate chat context, status form, interactive flows. |
| Production build | Passed | TypeScript compilation and Vite asset build. |
| Deployed HTTP smoke | 12 check groups passed | Real public URL, serverless API, and persistent Neon data. |

The 12 live groups checked:

1. Health endpoint and rejection of unauthenticated workspace access.
2. Two new accounts each starting with empty JDs, CVs, drafts, and comparisons.
3. Empty-chat guidance, wrong-password response, and duplicate-email response.
4. TXT JD/CV uploads, ranking order, evidence excerpts, summary, interview questions, grounded chat, and an unknown-fact answer.
5. Unrecorded status response, saving a stage and assessment, and chat citing that record.
6. Invitation and assessment draft creation and saved editing.
7. Cross-account candidate, JD, draft, and recruitment-status access returning `404`.
8. DOCX JD and PDF CV extraction, page location, and separate comparison results.
9. Simultaneous writes by different accounts with no candidate data crossing accounts.
10. Unsupported file, empty text, and file over 4 MiB returning validation errors.
11. Draft/candidate deletion, logout protection, login again, and saved Neon workspace recovery.
12. A long synthetic CV with compact workspace/ranking responses and a useful matching excerpt.

## Browser interface checks

| Journey | Observed |
| --- | --- |
| Create account | Registration worked; a new account showed zero candidates, no active role, and no preloaded sample names. Mismatched-password and unknown-email messages were checked earlier in Chrome. |
| Add materials | Separate JD and CV paste forms saved synthetic documents. Extracted required/preferred lists appeared; compare reflected the active JD. TXT/DOCX/PDF **file uploads** were exercised through the live HTTP test. |
| Explain a match | Ranked card displayed a donut, skill coverage bars, label, evidence chips, and a working **View evidence and prepare** action. Review showed a skill table, source line, summary, and interview questions. |
| Save status and ask | Review initially showed “No status recorded.” Saving **Recruiter screen** and an assessment note changed the panel. The floating icon opened chat with that candidate selected; chat reported the saved stage with one recruitment-record source. |
| Drafts | Invitation/assessment creation, edit, save, and copy were exercised in Chrome earlier in the session; backend persistence was checked on the live deployment. |
| Responsive/theme | Light/dark toggle, a 390-pixel mobile viewport, mobile navigation, and chat layout were checked earlier in Chrome. No horizontal overflow was observed at that width. |

An earlier UI review found a duplicate **Ask about candidate** button on the review page. It was removed; the floating chat icon remains the entry point, and the interface test confirms it opens with the candidate selected. A browser extension file chooser could not select local files because its file-URL permission was disabled. The API test covered TXT, DOCX, and PDF uploads on the deployed service; the visual picker itself was not automated through that extension.

## Visual/accessibility spot checks

The login form and main controls expose labels, error messages, a visible keyboard focus style, and named chat controls. A spot measurement of theme contrast found: light body 11.69:1, light muted text 5.56:1, light primary button 5.47:1; dark body 14.77:1, dark muted text 9.70:1, dark primary button 8.09:1. These values are samples of selected text/color pairs. No full screen-reader or WCAG audit was performed.

## Findings fixed during QA

- **Preloaded examples on new accounts:** the workspace initializer now creates an empty record. Existing accounts can explicitly remove known bundled examples while preserving their own uploads.
- **Empty-state errors:** compare, chat, and draft screens now give guidance before a JD or CV exists.
- **Large-document handling:** per-document limit is 4 MiB, below [Vercel's 4.5 MB request-body cap](https://vercel.com/docs/functions/limitations); responses use short excerpts so large CVs do not bloat routine requests.
- **Status answers without saved data:** chat now says “not recorded.” The review page lets the recruiter save the stage and assessment that chat later cites.
- **Duplicate chat action:** candidate review uses the floating chat launcher. The candidate remains selected when chat opens.
- **Optional LLM grounding:** an uncited model answer to a candidate-skill query falls back to the computed, cited answer.
- **Refresh after a release:** an already-open test tab could reuse an older HTML file whose JavaScript bundle had been removed, leaving a blank page. HTML now returns `Cache-Control: no-store`, and several prior versioned assets are retained in the deployed package so an older page can still load during the transition.
- **File chosen but JD not saved:** the PDF itself extracted correctly, but the former upload screen required an additional Add click after file selection. The user's CV was stored while the JD count stayed at zero, so comparison had no active role. File selection now starts upload automatically, and the empty comparison state names the missing JD. Duplicate-email registration now shows a direct login prompt.

## Remaining risks and test limits

- The live test simulated independent browsers with separate cookie jars and made simultaneous requests. We did not run a load test from many physical computers. The architecture uses per-account Postgres rows, and cross-account resource checks passed.
- Workspace revision checks prevent overlapping saves from silently overwriting one another. Older API clients that omit revision headers cannot detect changes that occurred before their request started.
- The optional Groq path was tested at the code level with a simulated model response, but the production QA run did not use a Groq key. Grounding checks reduce risk; they are not a proof that every generated sentence is true.
- No OCR for image-only PDFs, mail delivery, ATS integration, password recovery, email verification, abuse rate limiting, virus scanning, penetration test, full accessibility audit, bias evaluation, or measured ranking accuracy. Do not treat the alignment score as a hiring decision.
- The test accounts and synthetic documents created by the live smoke test persist in Neon; the script does not delete accounts. They contain no real candidate data.

## 7 November JD skill review update

The older counts above describe the previous deployed version. For the revised extraction and review flow, the local Python suite passed **50 tests**, the React suite passed **10 tests**, TypeScript compiled, and the production assets built. The revised 12-group HTTP smoke test passed against a temporary local server and then against the public Vercel/Neon deployment, including the new review gate. Two initial public attempts timed out during large synthetic uploads with a 35-second request limit; the test was rerun with a 90-second limit for large bodies and all groups passed. No app change was needed for those network timeouts.

All fourteen supplied JDs were parsed locally, without copying their original files to the repository or test database. In the final rerun the QA JD produced **17 required, 4 preferred, and 2 unspecified suggestions**; employer-background React and AWS were not suggested for that role. The frontend JD produced **6 required and 2 preferred**, and the newer backend JD **12 required, 4 preferred, and 1 unspecified**. SEO produced three unspecified suggestions; product, project, sales, evaluation, data science, and developer/designer documents also produced reviewable suggestions. The two files with multiple detected roles require a role selection before suggestions appear, so their initial preview has zero suggestions by design.

The probe also showed noisy short phrases in several documents, particularly product management, automotive evaluation, and developer/designer. Suggestions are **drafts with visible evidence**, not validated skills. The recruiter must remove or correct them before a score can appear. No general skill extraction accuracy is claimed from this small and varied sample. The score still depends on literal CV evidence and will miss some synonyms or experience stated indirectly.

## Workspace concurrency update

Workspace writes now use an atomic revision check. A forced overlap in the SQLite API tests returned one success and one conflict; a delete-versus-upload test verified the successful action remains saved. A separate synthetic account test against the configured Neon Postgres database also produced one success and one conflict, then removed the account. A stale-browser integration test used two sessions of the same account and verified an older edit was rejected. React tests cover retention of unsaved text, version binding, and retrying only CV files that were not already uploaded. The local and deployed HTTP smoke tests each passed all 12 groups. Chrome visual checks covered the desktop JD review screen, dark mode, and the mobile document screen and chat. The mobile launcher was moved into the header after it obscured a form field. The browser automation timed out on the native delete confirmation; automated backend and frontend tests cover the deletion path. Older API clients without revision headers cannot detect changes that occurred before their request started.

## Document management and shared library (local build)

The new build includes separate searches, department and tag metadata, candidate selection, multiple JD upload, and an opt-in library with original-file storage for new documents. Tests cover private defaults, cross-account denial, explicit publication, original downloads, independent copies, revocation, removal of shared legacy samples, and a copy-versus-revocation race. The updated 13-group local HTTP smoke test passed. A temporary isolated Neon schema passed owner isolation, sharing, exact text download, copy and revocation; the schema was removed after the test. An independent code reviewer identified and verified fixes for legacy-sample revocation, copy races, unavailable legacy downloads, and lost comparison selections. Chrome checks used synthetic documents to inspect dashboard counts, department and tag controls, shared-document preview, comparison selection, and the library in light, dark, and mobile layouts. The browser review seeded the synthetic shared item through the local API; automated backend tests cover publication and API behavior; the share confirmation was not exercised in Chrome.
