def test_fallback_rank_answer_uses_candidate_evidence():
    from backend.app.assistant import answer
    from backend.app.sample_data import sample_workspace

    workspace = sample_workspace()
    result = answer("Why is Maya ranked first?", workspace)
    assert "Maya" in result["text"]
    assert result["citations"]
    assert all(item["id"] in {e.id for c in workspace.candidates for e in c.evidence} for item in result["citations"])


def test_unknown_candidate_fact_is_not_invented():
    from backend.app.assistant import answer
    from backend.app.sample_data import sample_workspace

    result = answer("Does Maya have a professional certification?", sample_workspace())
    assert "not established" in result["text"].lower()


def test_summary_questions_and_email_draft_are_role_specific():
    from backend.app.assistant import generate_draft, generate_questions, generate_summary
    from backend.app.matching import rank
    from backend.app.sample_data import sample_workspace

    workspace = sample_workspace()
    jd = workspace.active_jd()
    candidate = workspace.candidates[0]
    match = next(x for x in rank(jd, workspace.candidates) if x.candidate_id == candidate.id)
    summary = generate_summary(jd, candidate, match)
    questions = generate_questions(jd, candidate, match)
    invitation = generate_draft("invitation", jd, candidate, "10 Nov 2026", "14:00 IST", "https://example.test/meet")
    assessment = generate_draft("assessment", jd, candidate, "12 Nov 2026", "", "https://example.test/task")
    assert candidate.name in summary
    assert jd.title in summary
    assert any("Airflow" in q for q in questions)
    assert "10 Nov 2026" in invitation and "Interview" in invitation
    assert "12 Nov 2026" in assessment and "assessment" in assessment.lower()
