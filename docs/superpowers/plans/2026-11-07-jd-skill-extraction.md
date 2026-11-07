# Evidence-led JD Skill Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract role-specific, evidence-backed JD skills across the supplied role families and require recruiter review before scoring.

**Architecture:** A pure Python extraction module turns source evidence into role options and requirement suggestions. The API stores approved requirements in the existing per-user workspace JSON, derives matching arrays for compatibility, and gates comparison while review is pending. React presents a compact review screen and reanalysis action.

**Tech Stack:** Python, FastAPI, pypdf, python-docx, React, TypeScript, Vitest, pytest, SQLite locally, Neon Postgres in deployment.

**Spec:** `docs/superpowers/specs/2026-11-07-jd-skill-extraction-design.md`

## Global Constraints

- No paid or required LLM API key for JD extraction.
- Do not commit the fourteen supplied JDs or upload them to the public test database.
- Source evidence must be retained for every automatic suggestion.
- Company background, benefits, and sibling roles must not silently become skill requirements.
- Required, preferred, and unspecified are distinct; alternative options count as one criterion.
- Unreviewed JDs and approved JDs with no scored skill criteria have no numeric comparison score.
- Existing manually edited skill arrays remain until a recruiter explicitly accepts a preview.

---

## File map

- Create `backend/app/skill_extraction.py`: normalize layout text, segment roles/sections, extract phrases and cues, return suggestions with evidence.
- Modify `backend/app/models.py`: store selected role, review metadata, and approved requirement records, with legacy JSON fallback.
- Modify `backend/app/main.py`: generate previews, validate/save approved records, and gate analysis for unreviewed JDs.
- Modify `backend/app/matching.py`: match alternative groups as one requirement and keep existing evidence behavior.
- Modify `backend/app/serializers.py`: expose review state and compact suggestions without full document text.
- Modify `frontend/src/App.tsx` and `frontend/src/styles.css`: role picker, skill review, reanalysis, and compare guidance.
- Add `tests/test_skill_extraction.py`; extend `tests/test_api.py`, `tests/test_matching.py`, and `frontend/src/App.test.tsx`.
- Update `README.md`, `docs/WORKING_SPEC.md`, `docs/QA_REPORT.md` after verification.

### Task 1: Extract requirements from JD structure

**Files:** Create `backend/app/skill_extraction.py`; test `tests/test_skill_extraction.py`.

**Interfaces:** `analyze_jd(evidence: list[Evidence], selected_role: str | None = None) -> dict` returns `roles`, `selected_role`, `suggestions`, and `warnings`. Each suggestion has `id`, `label`, `kind`, `category`, `options`, `source_id`, `source_location`, `source_quote`, `source_section`, and `origin`.

- [ ] Write synthetic failing tests for a company preamble, QA `added advantage`, frontend `Required`/`Preferred`, data scientist `plus`, backend `Nice-to-Have` and `or` group, HSE/SEO/sales phrases, and multiple role headings. Example:

```python
def test_company_tech_stack_does_not_become_qa_requirement():
    evidence = extract_paste("About us:\nWe use React and AWS.\nQA Engineer:\nRequirements:\nManual testing and Selenium.\nRest Assured is an added advantage.")
    result = analyze_jd(evidence)
    assert "React" not in [item["label"] for item in result["suggestions"]]
    assert {item["label"]: item["category"] for item in result["suggestions"]}["Rest Assured"] == "preferred"
```

- [ ] Run `./.venv/bin/python -m pytest -q tests/test_skill_extraction.py` and confirm failure from missing extractor behavior.
- [ ] Implement normalization, role/section segmentation, cue-based phrase extraction, shared canonical names, deduplication, and source locations in the new module. Keep candidate generation conservative; preserve unknown phrases as written.
- [ ] Run the focused tests and refine only observed failures. Confirm no ungrounded suggestion is emitted.
- [ ] Commit the extractor and its tests after fresh verification.

### Task 2: Persist review decisions and gate scoring

**Files:** Modify `backend/app/models.py`, `backend/app/main.py`, `backend/app/serializers.py`, `backend/app/matching.py`; tests `tests/test_api.py`, `tests/test_matching.py`.

**Interfaces:** `POST /api/jds/{id}/skills/preview` accepts `{selected_role?: str}` and returns an `analyze_jd` preview without mutation. `PUT /api/jds/{id}/skills` accepts `{selected_role: str, requirements: SkillRequirement[]}` and saves validated review data. Workspace JD responses expose `needs_review` and `selected_role`. Alternative groups are one scoring unit.

- [ ] Add failing API tests for upload needing review, preview without mutation, accepted review enabling score, legacy JD review, cross-account `404`, and invalid category/options rejection. Example:

```python
def test_uploaded_jd_needs_review_before_comparison(tmp_path):
    with make_client(tmp_path) as client:
        register(client, "review@example.test")
        jd = client.post("/api/jds/paste", json={"title": "QA", "text": "Required: Selenium."}).json()
        client.post("/api/candidates/paste", json={"name": "Example", "text": "Used Selenium."})
        assert jd["needs_review"] is True
        assert client.get("/api/compare").json()["results"] == []
```

- [ ] Add a failing matching test for `AWS or GCP or Azure` counting as one criterion when a CV mentions GCP.
- [ ] Run focused tests and confirm expected failures.
- [ ] Add model defaults and legacy loader behavior. Connect upload/paste to the extractor, add preview/save endpoints, derive approved arrays, and gate compare/analysis/chat statements while review is pending. Validate that automatic source IDs belong to that JD; allow manual entries only with `origin: manual`.
- [ ] Implement alternative-group matching with source excerpts. Keep the existing `required`/`preferred` response fields as derived compatibility values.
- [ ] Run focused tests and the full Python test suite; adapt old tests to explicitly approve their test JDs before asserting a score.
- [ ] Commit backend changes and tests after fresh verification.

### Task 3: Review skills in the interface

**Files:** Modify `frontend/src/App.tsx`, `frontend/src/styles.css`; test `frontend/src/App.test.tsx`.

**Interfaces:** The Documents view calls preview and save endpoints. It shows role options, grouped skill rows, source excerpts, add/remove/edit controls, **Save reviewed skills**, and **Cancel**. Compare and Overview use `needs_review` to avoid presenting a score for unreviewed JDs.

- [ ] Add failing React tests for upload opening review, multi-role selection, editing/removing/adding a skill, cancel leaving saved data intact, and reanalysis of a legacy JD. Example:

```typescript
test('unreviewed JD offers skill review', async () => {
  const pending = { ...sampleWorkspace, jds: [{ ...sampleWorkspace.jds[0], needs_review: true }] }
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return new Response('{}', { status: 401 })
    if (url.endsWith('/api/auth/register')) return Response.json({ email: 'review@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(pending)
    if (url.endsWith('/api/compare')) return Response.json({ jd: pending.jds[0], results: [] })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'review@example.test' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-demo-password' } })
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'long-demo-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  expect(screen.getByRole('button', { name: 'Review skills' })).toBeTruthy()
})
```

- [ ] Run `npm test` from `frontend` and confirm expected failures.
- [ ] Implement a compact review panel within Documents. Keep upload auto-save, then open review. Show source location beside each suggestion and a role picker when needed. Render unreviewed empty state in Compare and suppress stale Overview score.
- [ ] Run React tests and `npm run build`. Check keyboard controls and responsive layout.
- [ ] Commit UI changes and tests after fresh verification.

### Task 4: Cross-role QA, documentation, and deployment

**Files:** Update `README.md`, `docs/WORKING_SPEC.md`, `docs/QA_REPORT.md`; synthetic tests in the above test files if a case is missing.

**Interfaces:** No new public API. Acceptance is the specification's sample matrix and a live flow using synthetic documents only.

- [ ] Run the fourteen user-supplied JDs against a local isolated database, recording detected roles, required/preferred/unspecified suggestions, missing items, and false positives. Do not add these originals to the repository or Neon.
- [ ] For each material error, add a short synthetic failing regression test, run it red, make the smallest extractor correction, and run it green.
- [ ] Run `./.venv/bin/python -m pytest -q`, `npm test`, `npm run build`, and `git diff --check`; inspect output and fix real failures.
- [ ] Update setup, workflow, scoring, limitations, and observed local QA results in docs. Keep the prior QA report's historical claims identifiable as the earlier release.
- [ ] Commit verified changes, push the branch used by deployment, and exercise the public app with a synthetic JD and CV. Check a new JD review, saved review, comparison evidence, and an older JD's reanalysis path.
