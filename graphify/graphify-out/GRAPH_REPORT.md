# Graph Report - graphify  (2026-11-08)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 327 nodes · 899 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 44 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7814f09b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9

## God Nodes (most connected - your core abstractions)
1. `create_app()` - 92 edges
2. `workspace()` - 29 edges
3. `extract_paste()` - 26 edges
4. `JobDescription` - 22 edges
5. `Candidate` - 20 edges
6. `App()` - 19 edges
7. `save_workspace()` - 19 edges
8. `rank()` - 19 edges
9. `api()` - 18 edges
10. `Documents()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_jd_deletion_is_owner_scoped_and_selects_remaining_jd()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_document_ownership.py → backend/app/main.py
- `test_share_copy_revoke_and_delete_are_isolated()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_shared_library.py → backend/app/main.py
- `test_shared_pasted_document_preserves_original_whitespace()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_shared_library.py → backend/app/main.py
- `test_shared_upload_download_preserves_original_file()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_shared_library.py → backend/app/main.py
- `test_old_browser_version_cannot_overwrite_newer_edit()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_workspace_concurrency.py → backend/app/main.py

## Import Cycles
- None detected.

## Communities (12 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (49): Analysis, api(), ApiError, App(), logout(), refresh(), run(), AuthView() (+41 more)

### Community 1 - "Community 1"
Cohesion: 0.11
Nodes (39): StoredDocument, create_app(), active_jd(), add_pasted_candidate(), add_pasted_jd(), add_uploaded_candidate(), add_uploaded_jd(), candidate_analysis() (+31 more)

### Community 2 - "Community 2"
Cohesion: 0.10
Nodes (22): _chunks(), extract_document(), expect(), make_docx(), make_pdf(), request(), review_jd(), run() (+14 more)

### Community 3 - "Community 3"
Cohesion: 0.17
Nodes (28): answer(), _candidate(), _citation(), _fallback(), generate_draft(), generate_questions(), generate_summary(), canonical() (+20 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (22): Base, SharedDocument, WorkspaceRecord, publish(), test_old_account_can_remove_bundled_samples_without_losing_own_documents(), test_jd_deletion_is_owner_scoped_and_selects_remaining_jd(), test_copy_rechecks_revocation_before_committing(), test_removing_legacy_sample_revokes_its_shared_copy() (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (19): AuthStore, create_auth_store(), User, CandidateMetadata, ChatRequest, current_user(), login(), register() (+11 more)

### Community 6 - "Community 6"
Cohesion: 0.25
Nodes (16): extract_paste(), analyze_jd(), labels(), test_company_stack_is_not_a_qa_requirement(), test_frontend_required_and_preferred_sections(), test_generic_words_and_examples_are_not_independent_skills(), test_local_cue_does_not_make_previous_skill_required(), test_multiple_roles_require_selection_and_do_not_mix_requirements() (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.35
Nodes (14): make_client(), register(), review_jd(), test_chat_and_draft_work_without_api_key(), test_duplicate_email_explains_login_instead_of_creating_account(), test_empty_workspace_guides_chat_and_requires_a_jd_for_drafts(), test_first_workspace_requests_can_arrive_together(), test_pasted_candidate_is_isolated_by_account() (+6 more)

### Community 8 - "Community 8"
Cohesion: 0.34
Nodes (11): _alternative_group(), _category(), _clean(), _known_terms(), Line, _lines(), _novel_phrases(), _role_heading() (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.70
Nodes (4): client_for(), test_account_survives_new_app_instance(), test_registration_login_logout_and_protection(), test_wrong_credentials_have_same_error_and_duplicate_is_rejected()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `Community 1` to `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 9`?**
  _High betweenness centrality (0.303) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `create_app()` (e.g. with `AuthStore` and `User`) actually correct?**
  _`create_app()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.061507936507936505 - nodes in this community are weakly interconnected._
- **Why does `extract_paste()` connect `Community 6` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `JobDescription` (e.g. with `generate_draft()` and `generate_questions()`) actually correct?**
  _`JobDescription` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.11020408163265306 - nodes in this community are weakly interconnected._
- **Why does `analyze_jd()` connect `Community 6` to `Community 8`, `Community 1`, `Community 3`, `Community 5`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._