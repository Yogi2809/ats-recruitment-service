"""Keep API responses useful without returning entire stored CVs repeatedly."""

from .matching import ALIASES, canonical
from .models import Candidate, Evidence, JobDescription, MatchResult


def evidence_excerpt(evidence: Evidence, skill: str | None = None) -> dict:
    text = evidence.text
    offset = 0
    if skill:
        aliases = ALIASES.get(canonical(skill), [skill])
        positions = [text.lower().find(alias.lower()) for alias in aliases]
        positions = [position for position in positions if position >= 0]
        if positions:
            offset = max(0, min(positions) - 120)
    end = min(len(text), offset + 350)
    snippet = ("…" if offset else "") + text[offset:end] + ("…" if end < len(text) else "")
    return {"id": evidence.id, "source": evidence.source, "location": evidence.location, "text": snippet}


def jd_response(jd: JobDescription, include_evidence: bool = False) -> dict:
    return {
        "id": jd.id,
        "title": jd.title,
        "required": jd.required,
        "preferred": jd.preferred,
        "needs_review": jd.reviewed_at is None,
        "selected_role": jd.selected_role,
        "extractor_version": jd.extractor_version,
        "reviewed_requirements": jd.reviewed_requirements,
        "evidence": [evidence_excerpt(item) for item in jd.evidence[:20]] if include_evidence else [],
    }


def candidate_response(candidate: Candidate, include_evidence: bool = False) -> dict:
    return {
        "id": candidate.id,
        "name": candidate.name,
        "evidence": [evidence_excerpt(item) for item in candidate.evidence[:20]] if include_evidence else [],
    }


def match_response(match: MatchResult) -> dict:
    return {
        "candidate_id": match.candidate_id,
        "candidate_name": match.candidate_name,
        "score": match.score,
        "required_percent": match.required_percent,
        "preferred_percent": match.preferred_percent,
        "similarity_percent": match.similarity_percent,
        "matched_required": match.matched_required,
        "missing_required": match.missing_required,
        "matched_preferred": match.matched_preferred,
        "missing_preferred": match.missing_preferred,
        "evidence": {skill: evidence_excerpt(item, skill) for skill, item in match.evidence.items()},
    }
