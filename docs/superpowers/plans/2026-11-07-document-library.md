# Document management and shared library implementation plan

**Goal:** Make document management, comparison selection, and opt-in sharing useful and safe for multiple recruiters.

**Architecture:** Extend owner-scoped workspace records and add explicitly published snapshots with durable original-file storage. Continue to compute matches server-side from approved JD skills. Add accessible list controls and an improved chat within the existing React app.

**Tech stack:** FastAPI, SQLAlchemy, Postgres/SQLite, React, TypeScript, Vite.

**Spec:** docs/superpowers/specs/2026-11-07-document-library-design.md

1. Add owner-scoped JD deletion with a test covering cross-account denial and active-JD fallback. Add the corresponding confirmation control and test it.
2. Add independent search, multi-upload, department and tag metadata, and selection for comparisons. Test persistence and isolation, score updates, and UI empty and error states.
3. Add file storage and explicit share, unshare, list, download, and copy endpoints. Test two accounts, legacy/pasted files, revocation, and independent copies before building library UI.
4. Improve dashboard and chat, verify light and dark modes and mobile layout, run backend/frontend suites and a synthetic end-to-end test, and obtain an independent security and correctness review before deployment.
