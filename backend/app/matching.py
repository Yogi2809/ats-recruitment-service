import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Candidate, Evidence, JobDescription, MatchResult


ALIASES: dict[str, list[str]] = {
    "Python": ["python", "pyspark"],
    "SQL": ["sql", "postgresql", "postgres", "mysql", "snowflake", "bigquery"],
    "PostgreSQL": ["postgresql", "postgres"],
    "Airflow": ["airflow", "airflow dags", "apache airflow"],
    "Data Pipelines": ["data pipelines", "data pipeline", "etl", "elt"],
    "AWS": ["aws", "amazon web services", "ec2", "s3"],
    "React": ["react", "reactjs", "react.js"],
    "TypeScript": ["typescript"],
    "FastAPI": ["fastapi"],
    "Docker": ["docker", "containers"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Machine Learning": ["machine learning", "ml models"],
    "Manual Testing": ["manual testing", "manual qa"],
    "Test Cases": ["test cases", "test case", "test scenarios"],
    "Selenium": ["selenium", "selenium webdriver"],
    "API Testing": ["api testing", "api tests", "rest api testing"],
    "Jira": ["jira"],
    "Test Automation": ["test automation", "automation testing", "automated testing"],
}


def canonical(skill: str) -> str:
    for key in ALIASES:
        if skill.strip().lower() == key.lower():
            return key
    for key, aliases in ALIASES.items():
        if skill.strip().lower() in aliases:
            return key
    return skill.strip()


def find_skill(skill: str, chunks: list[Evidence]) -> Evidence | None:
    normalized = canonical(skill)
    aliases = ALIASES.get(normalized, [normalized.lower()])
    for chunk in chunks:
        for alias in aliases:
            match = re.search(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", chunk.text, re.I)
            if match:
                prefix = chunk.text[max(0, match.start() - 35) : match.start()].lower()
                if re.search(r"\b(?:no|without|lack|lacks|lacking|never used)\s+(?:direct\s+)?$", prefix):
                    continue
                return chunk
    return None


def _similarity(jd_text: str, cv_text: str) -> int:
    if not jd_text.strip() or not cv_text.strip():
        return 0
    matrix = TfidfVectorizer(stop_words="english").fit_transform([jd_text, cv_text])
    return round(float(cosine_similarity(matrix[0], matrix[1])[0][0]) * 100)


def rank(jd: JobDescription, candidates: list[Candidate]) -> list[MatchResult]:
    jd_text = " ".join(e.text for e in jd.evidence)
    results = []
    for candidate in candidates:
        hits = {skill: find_skill(skill, candidate.evidence) for skill in jd.required + jd.preferred}
        matched_required = [skill for skill in jd.required if hits[skill]]
        matched_preferred = [skill for skill in jd.preferred if hits[skill]]
        required = round(100 * len(matched_required) / len(jd.required)) if jd.required else 0
        preferred = round(100 * len(matched_preferred) / len(jd.preferred)) if jd.preferred else 0
        similarity = _similarity(jd_text, " ".join(e.text for e in candidate.evidence))
        factors = [(10, similarity)]
        if jd.required:
            factors.append((70, required))
        if jd.preferred:
            factors.append((20, preferred))
        score = round(sum(weight * value for weight, value in factors) / sum(weight for weight, _ in factors))
        results.append(
            MatchResult(
                candidate.id,
                candidate.name,
                score,
                required,
                preferred,
                similarity,
                matched_required,
                [skill for skill in jd.required if not hits[skill]],
                matched_preferred,
                [skill for skill in jd.preferred if not hits[skill]],
                {skill: evidence for skill, evidence in hits.items() if evidence is not None},
            )
        )
    return sorted(results, key=lambda item: (-item.score, item.candidate_id))
