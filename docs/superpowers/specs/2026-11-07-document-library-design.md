# Recruiter document management and shared library

Approved direction: private workspaces with optional explicit publication to a read-only shared library. Owners control their source documents. Never expose historical uploads by default.

Recruiters can add multiple JDs or CVs through separate upload controls, search each collection independently, view and delete their own documents, group JDs by department, tag and filter candidates, and choose one JD and any subset of CVs to compare. An edited skill list refreshes comparison. Dashboard counts navigate to their lists; review prompts state the actual next step.

Each shared item is an explicit snapshot. Only authenticated users can list, view, download, or copy it into their own workspace. Unsharing or deleting the owner's source removes the shared listing; copies already imported remain with their recipient. Stored originals require durable database-backed binary storage; older uploads lack originals and must be labeled accordingly. Pasted documents can be downloaded as text. New accounts and uploads are private by default. Every read, mutation, and download checks owner or publication permission on the server.

Keep role review as a score gate, simplify its display, improve chat readability and feedback, preserve light/dark responsive layout, and keep the optional server-side Groq integration with a no-key fallback. Use synthetic data in tests. Verify owner isolation, publication and revocation, files, list controls, comparison refresh, mobile/desktop and both themes. No claims of universal extraction accuracy or verified hiring outcomes.
