from backend.app.documents import extract_paste
from backend.app.skill_extraction import analyze_jd


def labels(text: str, role: str | None = None) -> dict[str, str]:
    return {item["label"]: item["category"] for item in analyze_jd(extract_paste(text), role)["suggestions"]}


def test_company_stack_is_not_a_qa_requirement():
    found = labels(
        "About us:\nWe use React and AWS.\nQA Engineer:\nRequirements:\n"
        "Manual Testing, Selenium, and API Testing.\nRest Assured is an added advantage."
    )
    assert "React" not in found
    assert "AWS" not in found
    assert found["Manual Testing"] == "required"
    assert found["Selenium"] == "required"
    assert found["Rest Assured"] == "preferred"


def test_frontend_required_and_preferred_sections():
    found = labels(
        "Front-End Developer Job Description\nJob Skills & Qualifications\nRequired:\n"
        "Working knowledge of HTML, CSS, JS, Jquery.\nPreferred:\n"
        "Experience with Bootstrap framework and DOM manipulation."
    )
    assert all(found[item] == "required" for item in ["HTML", "CSS", "JavaScript", "jQuery"])
    assert found["Bootstrap"] == "preferred"
    assert found["DOM Manipulation"] == "preferred"


def test_required_and_preferred_cues_can_share_one_line():
    found = labels("Data Engineer\nRequired skills: Python, SQL, and data pipelines. Preferred: AWS.")
    assert found["Python"] == "required"
    assert found["SQL"] == "required"
    assert found["Data Pipelines"] == "required"
    assert found["AWS"] == "preferred"


def test_plus_cue_overrides_general_skillset_heading():
    found = labels(
        "Data Scientist\nSkillsets:\nExpert on R.\nKnowing Python is a plus.\n"
        "SPSS or Weka would be an added advantage."
    )
    assert found["R"] == "unspecified"
    assert found["Python"] == "preferred"
    assert found["SPSS or Weka"] == "preferred"


def test_nice_to_have_and_alternative_group_count_as_one_suggestion():
    result = analyze_jd(extract_paste(
        "Backend Developer\nRequired Skills & Qualifications:\n"
        "Familiarity with cloud platforms (AWS, GCP, or Azure).\n"
        "Nice-to-Have:\nKnowledge of GraphQL or gRPC."
    ))
    groups = {item["label"]: item for item in result["suggestions"]}
    assert groups["AWS or GCP or Azure"]["options"] == ["AWS", "GCP", "Azure"]
    assert groups["AWS or GCP or Azure"]["category"] == "required"
    assert groups["GraphQL or gRPC"]["category"] == "preferred"


def test_unfamiliar_role_phrases_keep_evidence_without_a_per_role_catalog():
    found = analyze_jd(extract_paste(
        "HSE Safety Manager\nResponsibilities:\nFacilitate hazard identification and risk assessment.\n"
        "Requirements:\nKnowledge of ISO 45001:2018 and incident investigation."
    ))["suggestions"]
    assert any("hazard identification" in item["label"].lower() for item in found)
    assert any("incident investigation" in item["label"].lower() for item in found)
    assert all(item["source_quote"] and item["source_location"] for item in found)


def test_multiple_roles_require_selection_and_do_not_mix_requirements():
    evidence = extract_paste(
        "RA\nJob Responsibilities:\nExcellent negotiation skills.\n"
        "RM\nJob Responsibilities:\nSales planning and coaching.\n"
        "CJ\nJob Responsibilities:\nCar inspection and repair estimation."
    )
    preview = analyze_jd(evidence)
    assert preview["roles"] == ["RA", "RM", "CJ"]
    assert preview["selected_role"] is None
    assert preview["suggestions"] == []
    ra = analyze_jd(evidence, "RA")
    assert any("negotiation" in item["label"].lower() for item in ra["suggestions"])
    assert not any("car inspection" in item["label"].lower() for item in ra["suggestions"])


def test_title_detection_ignores_prose_and_reporting_lines():
    result = analyze_jd(extract_paste(
        "PRODUCT MANAGER\nLeader: Executive Vice President of Operations and Travel Technology\n"
        "The requirements must be met by an associate to perform the essential functions.\n"
        "Required Skills & Qualifications:\nProduct roadmap and market research."
    ))
    assert result["roles"] == ["PRODUCT MANAGER"]
    assert {"Product Roadmap", "Market Research"} <= {s["label"] for s in result["suggestions"]}


def test_required_skills_and_qualifications_heading_and_experience_line():
    found = labels(
        "Backend Developer\nRequired Skills & Qualifications:\n"
        "Experience with Node.js and REST API.\n"
        "Experience with SQL and Python.\n"
        "Nice-to-Have:\nKnowledge of Kafka."
    )
    assert all(found[s] == "required" for s in ["Node.js", "REST API", "SQL", "Python"])
    assert found["Kafka"] == "preferred"


def test_local_cue_does_not_make_previous_skill_required():
    found = labels("Data Scientist\nSkillsets:\nExpert on R. (Excellent coding aptitude is required.)")
    assert found["R"] == "unspecified"


def test_generic_words_and_examples_are_not_independent_skills():
    found = labels(
        "React.JS Developer\nRequired:\nExperience with React and Web.\n"
        "Experience with JavaScript and DOM manipulation.\n"
        "Evaluation Engineer\nRequirements:\nExperience with engines (Hyundai, Toyota, BMW)."
    , role="React.JS Developer")
    assert "React" in found
    assert "Web" not in found
    assert "The" not in found


def test_title_with_company_suffix_is_one_role():
    result = analyze_jd(extract_paste(
        "Data Scientist- Cars24.com (3-5 years)\nSkillsets:\nExperience with Python."
    ))
    assert result["roles"] == ["Data Scientist"]


def test_repeated_skill_has_one_review_row_and_required_priority():
    result = analyze_jd(extract_paste(
        "QA Engineer\nPreferred:\nSelenium is a plus.\n"
        "Requirements:\nSelenium and Python are required."
    ))
    selenium = [s for s in result["suggestions"] if s["label"] == "Selenium"]
    assert len(selenium) == 1
    assert selenium[0]["category"] == "required"
