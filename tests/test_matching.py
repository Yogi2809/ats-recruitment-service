def test_skill_aliases_and_missing_evidence():
    from backend.app.documents import extract_paste
    from backend.app.matching import rank
    from backend.app.models import Candidate, JobDescription

    jd = JobDescription("jd", "Data Engineer", ["Python", "SQL", "Airflow"], ["AWS"], extract_paste("Python SQL Airflow AWS"))
    strong = Candidate("strong", "Strong", extract_paste("Built Python services using PostgreSQL and Airflow DAGs on AWS."))
    partial = Candidate("partial", "Partial", extract_paste("Python and PostgreSQL reporting. No Airflow experience."))
    results = rank(jd, [partial, strong])
    assert [result.candidate_id for result in results] == ["strong", "partial"]
    assert results[0].matched_required == ["Python", "SQL", "Airflow"]
    assert results[1].missing_required == ["Airflow"]
    assert results[0].evidence["SQL"].text.startswith("Built Python")


def test_score_uses_documented_weights_and_ties_are_stable():
    from backend.app.documents import extract_paste
    from backend.app.matching import rank
    from backend.app.models import Candidate, JobDescription

    jd = JobDescription("jd", "Engineer", ["Python", "Airflow"], ["AWS"], extract_paste("Python Airflow AWS"))
    first = Candidate("a", "A", extract_paste("Python AWS"))
    second = Candidate("b", "B", extract_paste("Python AWS"))
    results = rank(jd, [second, first])
    assert [x.candidate_id for x in results] == ["a", "b"]
    assert results[0].required_percent == 50
    assert results[0].preferred_percent == 100
    assert results[0].score == round(35 + 20 + results[0].similarity_percent * 0.1)
