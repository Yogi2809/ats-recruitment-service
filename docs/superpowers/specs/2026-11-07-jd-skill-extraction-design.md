# RoleTrace: evidence-led JD skill extraction

**Date:** 7 November 2026

**Status:** Reviewed against implementation and fourteen supplied JDs; implemented with recruiter approval as the score gate
**Scope:** Replace the current JD skill inference and add a recruiter review step before those skills influence comparison. CV upload, authentication, email drafts, and chat remain in their current flows.

## Problem and evidence

RoleTrace currently scans every PDF page for a small fixed alias list, assigns all hits to `required` unless it sees a literal `Required:` or `Preferred:` marker, and saves the resulting arrays when the JD is added. Stored arrays are not refreshed when the extractor changes. The QA JD saved before the latest alias expansion therefore shows SQL, AWS, React, and Python, largely from the employer overview. Running that same PDF through the latest code yields ten required skills and no preferred skills; the added-advantage items are still missed.

All fourteen supplied JDs parsed successfully in an isolated local probe. Nine yielded no skills, three yielded one, two yielded more than one, and none yielded preferred skills. The set spans QA, backend and frontend development, data science, SEO, product and project management, sales, automotive evaluation, and HSE. It includes a file with three roles and another with two roles. These supplied documents are test inputs only; do not copy the originals into the public repository or live test database. Build committed tests from short synthetic excerpts that reproduce their structures.

## User outcome

After adding a JD, the recruiter sees a short review of detected requirements, each tied to words in the document. They can choose the role when a document contains several, correct required/preferred/unspecified classification, remove irrelevant items, add a missing item, and then save the reviewed list. Comparison scores appear only after that review. An existing JD offers **Reanalyse skills** without overwriting edits until the recruiter accepts the preview.

The app must never imply that a missing CV mention proves a candidate lacks a skill. The score remains RoleTrace's explainable JD alignment, not a hiring decision or an external ATS score.

## Approaches considered

1. **Per-role dictionaries:** simple for one JD but unbounded maintenance and weak across the supplied nontechnical roles.
2. **A very large skills taxonomy alone:** helps name normalization, but cannot determine whether a term is an employer technology, a requirement, a preference, or one of several alternatives.
3. **Chosen: document structure + open phrase candidates + shared normalization + human review:** handles unseen role phrases without a paid API. A moderate shared vocabulary improves canonical names; the original text remains the authority. A downloadable taxonomy such as ESCO may enrich normalization later, after measuring this version.

No hosted LLM or API key is needed for the core flow. A future LLM may suggest candidates, but cannot bypass evidence and recruiter approval.

## Extraction pipeline

The pipeline has separate, testable units:

1. **Document text and locations.** Keep PDF page, DOCX paragraph/table, or pasted-line locations. Normalize ligatures, whitespace, broken line wraps, bullets, and common OCR-like spacing artifacts without changing the saved source text. If a PDF contains no readable text, retain the existing clear error.
2. **Document and role segmentation.** Detect headings and spans for role title(s), company background, responsibilities, qualifications, requirements, preferences, benefits, and boilerplate. Repeated headers/footers and employer technology overviews do not generate requirements. When clear multiple role headings occur, offer those roles and do not combine their spans. If segmentation is uncertain, show the ambiguity and require review; do not silently combine roles.
3. **Candidate phrases.** Within the selected role's relevant sections, identify explicit tools and named methods from a shared vocabulary *and* phrases from bullet and cue patterns such as “experience with X,” “knowledge of X,” “ability to X,” and “X skills.” Split coordinated lists and slash-separated tools, but preserve meaningful phrases such as “hazard identification,” “link building,” and “test plan design.” Do not invent terms that have no supporting span. Treat responsibilities as suggested capabilities, not automatically as mandatory requirements.
4. **Requirement language.** Classify local cues including `must`, `required`, `essential`, `preferred`, `desired`, `nice-to-have`, `plus`, and `added advantage`. A cue can apply to a heading, bullet, or clause. Use `unspecified` when language is not explicit. Retain `A or B or C` as one alternative group so that matching any option satisfies one criterion. A comma list without `or` remains separate items. Education, years of experience, licenses, travel, and schedule are recorded as non-skill requirements for review but excluded from the skill score.
5. **Normalization and evidence.** Map recognized aliases to a canonical label; preserve novel phrases as written. Each suggestion includes its category, short source quote, location, source section, and whether it is an alternative group. Deduplicate exact labels within a role, without merging distinct skills merely because their words overlap. The current record retains the strongest category and one supporting quote when a term occurs more than once; collecting all supporting spans is future work.

This first version uses transparent Python parsing and a manageable shared alias catalog. It aims for useful suggestions and honest uncertainty, not perfect autonomous extraction of every skill in every occupation.

## Data and API design

Add a reviewed requirement record to the stored JD JSON, without exposing another account's material:

```text
SkillRequirement {
  id, label, kind: skill | other_requirement,
  category: required | preferred | unspecified,
  options: [label, ...], source_id, source_location, source_quote,
  source_section, origin: suggested | manual
}
JobDescription adds selected_role, extractor_version, reviewed_at,
and reviewed_requirements. Existing required/preferred arrays stay in API
responses for the current comparison, chat, and display code.
```

`required` and `preferred` are derived from approved `kind: skill` records. An alternative group contributes **one** criterion to coverage and is found when the CV supports any option. `unspecified` and `other_requirement` records are shown for review but do not enter the skill score. A manually added term without a JD source is visibly marked **Added by recruiter** and can be included only after explicit save. If the approved JD has no required or preferred skill criteria, comparison shows **No skill score available** rather than a similarity-only percentage.

API behavior:

- `POST /api/jds/paste` and `/api/jds/upload` save source evidence and return `needs_review: true`. They may return a compact preview; full preview remains available after reload.
- `POST /api/jds/{id}/skills/preview` takes an optional role selection and returns role choices, candidate records, and warnings. It is read-only with respect to the saved JD.
- `PUT /api/jds/{id}/skills` validates a chosen role and edited records, saves them as reviewed, updates derived arrays, and returns the JD. IDs, categories, options, and text lengths are validated server-side. A preview from one account cannot update another account's JD.
- `GET /api/compare` and candidate analysis return a review-needed state rather than a numeric score while the active JD is unreviewed. They resume immediately after saving reviewed skills.
- Existing JDs with no extractor version retain their source text and old lists but are flagged for review. **Reanalyse skills** previews a new list; it never silently replaces prior manual edits. The recruiter can accept, edit, or cancel. Saving the review updates the score.

Workspace JSON remains per account. Reanalysis must operate on one JD and preserve all other workspaces, candidates, statuses, and drafts. No original document is uploaded to a third-party inference service.

## Interface flow

Keep the current simple Documents page. After a JD upload or paste, show **Review skills to enable comparison** and open a focused review panel. Show the detected role at the top; when multiple roles exist, the recruiter chooses one before saving. Group rows as **Required**, **Preferred**, **Unspecified**, and **Other requirements**. Each row has an editable label/category, remove action, and expandable source quote with page or paragraph. Alternative groups display options together. The recruiter can add a missing skill. Use short copy and avoid a dense dashboard.

For an already saved JD, show **Reanalyse skills** next to **Edit skills**. Previewing changes does not mutate the JD; **Save reviewed skills** applies them, **Cancel** leaves it untouched. If extraction finds no credible suggestions, say so and invite manual entry. The comparison page explains which JD needs review and links back to Documents. The floating chat remains available, but must not describe unreviewed scores as facts.

## Failure handling and boundaries

- Empty or unreadable file: existing upload error; do not create a scored JD.
- Very long company preamble: retain it as source, exclude it from requirement suggestions.
- Unclear section or phrase: mark `unspecified` or show a review warning; do not force `required`.
- Multiple roles: require role selection; never merge their skill lists by default.
- Alternative options: one grouped criterion; do not score each option as an independent must-have.
- Novel term: retain its literal phrase and evidence. CV matching may use conservative normalization, but a semantic guess without a supporting CV excerpt cannot be a **Found** result.
- Existing manual skills: keep them until a recruiter accepts a replacement preview.
- Duplicate or conflicting terms: show one canonical item with all source references where possible; explicit preference wording takes precedence only for that local occurrence, and conflicts remain visible for review.

## Validation and acceptance

Use focused unit tests for segmentation, phrase candidates, cue classification, alternatives, alias normalization, and legacy records; API tests for preview/save/isolation and score gating; React tests for review and reanalysis. Exercise the fourteen supplied JDs locally, without committing or publicly uploading them, and record the observed outputs in a QA report. Commit synthetic excerpts for regression tests across the covered role families.

Minimum acceptance examples:

- QA JD: testing requirements come from the QA role; React/AWS in the employer overview do not become QA requirements; “added advantage” tools are preferred.
- Frontend JD: HTML/CSS/JavaScript/jQuery appear under required; Bootstrap and DOM manipulation under preferred.
- Data scientist JD: Python “is a plus” is preferred, not required.
- Backend JD: “Nice-to-Have” items are preferred; AWS/GCP/Azure is one alternative group.
- Sales, SEO, product/project management, evaluation, and HSE samples produce role-specific suggestions or explicit review warnings instead of a silent empty skill list.
- Multi-role files require role selection, and selected-role evidence does not include sibling-role requirements.
- Legacy QA JD shows a review prompt; reanalysis and accepted edits change comparisons, while cancel leaves saved data unchanged.
- Every accepted automatic skill has a verifiable source location. Every result is isolated to its owner account.

The fourteen samples are a diverse probe, not a representative benchmark of all occupations. We will report exact observed errors and avoid claiming general accuracy from this small set.
