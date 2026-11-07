"""Suggest JD requirements from role text, retaining the line that supports each suggestion.

This deliberately produces reviewable candidates rather than declaring an autonomous
reading of a job description to be final.
"""

from dataclasses import dataclass
import re
import unicodedata

from .matching import ALIASES
from .models import Evidence


EXTRA_TERMS: dict[str, list[str]] = {
    "HTML": ["html", "html5"], "CSS": ["css", "css3"],
    "JavaScript": ["javascript", "js"], "jQuery": ["jquery"],
    "Bootstrap": ["bootstrap"], "DOM Manipulation": ["dom manipulation"],
    "R": ["r"], "SPSS": ["spss"], "Weka": ["weka"],
    "Rest Assured": ["rest assured", "rest-assured"],
    "HttpClient": ["httpclient", "http client"], "BDD": ["bdd", "behavior driven development"],
    "Cucumber": ["cucumber"], "Appium": ["appium"],
    "Jenkins": ["jenkins"], "Git": ["git"], "GitHub": ["github"],
    "Confluence": ["confluence"], "Java": ["java"], "Groovy": ["groovy"],
    "SoapUI": ["soap ui", "soapui"], "JMeter": ["jmeter"],
    "CI/CD": ["ci/cd", "continuous integration", "ci tool"],
    "Node.js": ["node.js", "nodejs"], "GCP": ["gcp", "google cloud"],
    "Azure": ["azure"], "GraphQL": ["graphql"], "gRPC": ["grpc"],
    "Kafka": ["kafka"], "RabbitMQ": ["rabbitmq"],
    "MongoDB": ["mongodb"], "MySQL": ["mysql"],
    "Redux": ["redux"], "Flux": ["flux"],
    "Webpack": ["webpack", "web-pack", "web pack"], "NPM": ["npm"],
    "Linux": ["linux"], "REST API": ["rest api", "restful api", "rest api development"],
    "C#": ["c#"], "ASP.NET": ["asp.net"], "WCF": ["wcf"],
    "Unit Testing": ["unit testing"], "Dependency Injection": ["dependency injection"],
    "SEO": ["seo", "search engine optimization"],
    "Google Analytics": ["google analytics"], "Link Building": ["link building"],
    "Hazard Identification": ["hazard identification"],
    "Risk Assessment": ["risk assessment"],
    "Incident Investigation": ["incident investigation"],
    "ISO 14001": ["iso 14001"], "ISO 45001": ["iso 45001"],
    "ISO 9001": ["iso 9001"], "OSHA 10": ["osha 10"],
    "Negotiation": ["negotiation"], "Car Inspection": ["car inspection"],
    "Repair Estimation": ["repair estimation"],
    "Sales Planning": ["sales planning"], "Coaching": ["coaching"],
    "Project Management": ["project management"],
    "Product Roadmap": ["product roadmap"],
    "Market Research": ["market research"],
    "Tableau": ["tableau"], "Power BI": ["power bi"],
    "Forecasting": ["forecasting"], "Regression": ["regression"],
}

TERMS = {**ALIASES, **EXTRA_TERMS}
ROLE_WORDS = re.compile(r"\b(?:engineer|developer|designer|manager|scientist|officer|analyst|specialist|associate|executive|jockey)\b", re.I)
BACKGROUND = re.compile(r"^(?:about\b|why join us|our values|our team|benefits|perks|disclosures|employee practices|where are we|the problem|why is the problem|what can we create|how do we do it|few stats|faq|our captains)", re.I)
ROLE_SECTION = re.compile(r"^(?:job |key |principal |roles?\s*(?:&|and)\s*)?responsibilit(?:y|ies)|^ideal candidate profile|^desired candidate profile|^about the role|^specific duties|^essential functions|^broad responsibility", re.I)
REQUIRED_SECTION = re.compile(r"^(?:requirements?|required(?: skills| qualifications| experience)?|essential qualifications|qualifications?(?: for .+)?|training, skills|competency and position requirements|experience required|must have|we are looking for)", re.I)
PREFERRED_SECTION = re.compile(r"^(?:preferred|nice[- ]to[- ]have|desired to have|good to have)", re.I)
UNSPECIFIED_SECTION = re.compile(r"^(?:skillsets?|specific skills|job skills|experience|competenc(?:y|ies))\b", re.I)
OTHER_SECTION = re.compile(r"^(?:education|physical factors|working conditions|schedule|quality and quantity standards)\b", re.I)
PREFERRED_CUE = re.compile(r"\b(?:preferred|nice[- ]to[- ]have|desired|plus|added advantage|would be an advantage|optional)\b", re.I)
REQUIRED_CUE = re.compile(r"\b(?:must(?:\s+have)?|mandatory|required|essential)\b", re.I)
QUALIFICATION_CUE = re.compile(r"\b(?:bachelor|degree|diploma|years? of experience|driv(?:er|ing)'?s? licen[cs]e|travel|work location|shift)\b", re.I)
SKILL_CUE = re.compile(r"\b(?:experience (?:with|in|on)|knowledge of|proficiency in|proficient in|familiarity with|expert on|understanding of|skills? (?:in|with)|ability to|capability to)\s+(.+)", re.I)
ACTION_START = re.compile(r"^(?:develop|design|implement|manage|create|conduct|perform|facilitate|coordinate|prepare|analyse|analyze|build|optimize|monitor|ensure|maintain|lead|guide|work with|evaluate|carry out|automate|test|support|estimate|handle|review|provide|produce|deliver)\b\s*", re.I)
STOP_TAIL = re.compile(r"\b(?:based on|in order to|so that|to ensure|for the purpose of|before release|as needed|as per|according to|using)\b", re.I)


@dataclass(frozen=True)
class Line:
    index: int
    text: str
    evidence: Evidence


def _clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip(" \t\r\n\u2022●o")


def _lines(evidence: list[Evidence]) -> list[Line]:
    rows = []
    for item in evidence:
        for raw in item.text.splitlines():
            cleaned = _clean(raw)
            if cleaned:
                rows.append(Line(len(rows), cleaned, item))
    return rows


def _role_heading(text: str, next_text: str = "") -> str | None:
    plain = text.strip(" :-–—")
    if re.fullmatch(r"[A-Z]{2,4}", plain) and re.search(r"job responsibilities", next_text, re.I):
        return plain
    explicit = re.match(r"^(?:job role|job title|position(?: title)?|general job title)\s*[:\-–]\s*(.+)$", plain, re.I)
    if explicit:
        plain = explicit.group(1).strip()
    if len(plain) > 75 or not ROLE_WORDS.search(plain):
        return None
    if re.search(r"\b(?:experience|knowledge|proficiency|responsibilities|requirements|qualifications|candidate|team|our|looking|years?)\b", plain, re.I):
        return None
    if re.search(r"[.!?]", plain) and not re.search(r"(?:React\.JS|Node\.JS|Sr\.)", plain, re.I):
        return None
    plain = re.sub(r"^(?:job description\s*[-–:]?\s*|kra for\s+)", "", plain, flags=re.I)
    plain = re.sub(r"\s+job description$", "", plain, flags=re.I)
    return plain.strip(" :-–—") or None


def _roles(lines: list[Line]) -> tuple[list[str], list[tuple[int, str]]]:
    positions = []
    unique = []
    for i, line in enumerate(lines):
        role = _role_heading(line.text, lines[i + 1].text if i + 1 < len(lines) else "")
        if role is None:
            continue
        normalized = re.sub(r"\W+", "", role.lower())
        existing = next((name for name in unique if normalized in re.sub(r"\W+", "", name.lower()) or re.sub(r"\W+", "", name.lower()) in normalized), None)
        canonical = existing or role
        if existing is None:
            unique.append(canonical)
        positions.append((i, canonical))
    return unique, positions


def _section(text: str) -> tuple[str | None, str]:
    stripped = text.strip(" :-–—")
    for pattern, name in [
        (BACKGROUND, "background"), (PREFERRED_SECTION, "preferred"),
        (REQUIRED_SECTION, "required"), (ROLE_SECTION, "responsibilities"),
        (OTHER_SECTION, "other"), (UNSPECIFIED_SECTION, "unspecified"),
    ]:
        if pattern.match(stripped):
            if ":" in text:
                prefix, remainder = text.split(":", 1)
                if len(prefix.split()) <= 6:
                    return name, remainder.strip()
            if len(stripped.split()) <= 5 and not text.endswith("."):
                return name, ""
    return None, text


def _category(text: str, section: str) -> str:
    if PREFERRED_CUE.search(text):
        return "preferred"
    if REQUIRED_CUE.search(text):
        return "required"
    return section if section in {"required", "preferred"} else "unspecified"


def _known_terms(text: str) -> list[tuple[int, int, str]]:
    found = []
    for label, aliases in TERMS.items():
        for alias in sorted(set([label.lower(), *aliases]), key=len, reverse=True):
            for match in re.finditer(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", text, re.I):
                found.append((match.start(), match.end(), label))
    found.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    kept = []
    for hit in found:
        if not any(hit[0] >= prior[0] and hit[1] <= prior[1] for prior in kept):
            kept.append(hit)
    return kept


def _alternative_group(text: str, terms: list[tuple[int, int, str]]) -> list[str]:
    if not re.search(r"\bor\b", text, re.I):
        return []
    # A role's alternative tools are a single requirement; do not group unrelated
    # skills elsewhere in a long sentence.
    clauses = re.split(r"[.;]", text)
    for clause in clauses:
        if not re.search(r"\bor\b", clause, re.I):
            continue
        labels = []
        for _, _, label in _known_terms(clause):
            if label not in labels:
                labels.append(label)
        if 2 <= len(labels) <= 4 and re.search(r"\b(?:or|and/or)\b", clause, re.I):
            return labels
    return []


def _novel_phrases(text: str) -> list[str]:
    candidates = []
    cue = SKILL_CUE.search(text)
    if cue:
        phrase = cue.group(1)
        phrase = re.split(r"\b(?:is a plus|would be an added advantage|will be an added advantage)\b", phrase, maxsplit=1, flags=re.I)[0]
        phrase = STOP_TAIL.split(phrase, maxsplit=1)[0]
        for part in re.split(r",|\s+and\s+|\s*&\s*", phrase):
            part = part.strip(" .:;()")
            part = re.sub(r"^(?:the|a|an|good|strong|excellent|working|basic)\s+", "", part, flags=re.I)
            if 1 <= len(part.split()) <= 5 and len(part) >= 3:
                candidates.append(part)
    elif ACTION_START.match(text):
        phrase = ACTION_START.sub("", text, count=1)
        phrase = STOP_TAIL.split(phrase, maxsplit=1)[0]
        phrase = re.split(r"[.;]", phrase, maxsplit=1)[0]
        for part in re.split(r",|\s+and\s+|\s*&\s*", phrase):
            part = part.strip(" .:;()")
            if 1 <= len(part.split()) <= 5 and len(part) >= 4:
                candidates.append(part)
    return candidates


def _suggestions(lines: list[Line], role_positions: list[tuple[int, str]], selected_role: str | None) -> list[dict]:
    section = "unspecified"
    suggestions: list[dict] = []
    seen: set[tuple[str, str]] = set()
    active_role = None
    for line in lines:
        role_at_line = next((role for index, role in role_positions if index == line.index), None)
        if role_at_line:
            active_role = role_at_line
            section = "unspecified"
            continue
        if selected_role and active_role and active_role != selected_role:
            continue
        if role_positions and not active_role:
            continue
        new_section, content = _section(line.text)
        if new_section:
            section = new_section
            if not content:
                continue
        if section in {"background", "other"}:
            continue
        text = content.strip(" -•\u2022●")
        if not text or re.search(r"(?:https?://|www\.|@|\b(?:page|tel|phone|cin)\b)", text, re.I):
            continue
        category = _category(text, section)
        kind = "other_requirement" if QUALIFICATION_CUE.search(text) and not _known_terms(text) else "skill"
        terms = _known_terms(text)
        alternatives = _alternative_group(text, terms)
        groups: list[tuple[str, list[str]]] = []
        if alternatives:
            groups.append((" or ".join(alternatives), alternatives))
            terms = [hit for hit in terms if hit[2] not in alternatives]
        groups.extend((label, [label]) for _, _, label in terms)
        if kind == "skill":
            for phrase in _novel_phrases(text):
                if any(phrase.lower() in label.lower() or label.lower() in phrase.lower() for label, _ in groups):
                    continue
                if re.search(r"\b(?:experience|candidate|team|role|products?|company|etc|years?)\b", phrase, re.I):
                    continue
                groups.append((phrase[0].upper() + phrase[1:], [phrase]))
        if kind == "other_requirement" and not groups:
            groups.append((text[:100], [text[:100]]))
        for label, options in groups:
            key = (label.casefold(), category)
            if key in seen:
                continue
            seen.add(key)
            suggestions.append({
                "id": f"{line.evidence.id}:{line.index}:{len(suggestions)}",
                "label": label,
                "kind": kind,
                "category": category,
                "options": options,
                "source_id": line.evidence.id,
                "source_location": line.evidence.location,
                "source_quote": text[:350],
                "source_section": section,
                "origin": "suggested",
            })
    return suggestions


def analyze_jd(evidence: list[Evidence], selected_role: str | None = None) -> dict:
    """Return reviewable role-specific skill suggestions from saved document evidence."""
    lines = _lines(evidence)
    roles, positions = _roles(lines)
    if selected_role and selected_role not in roles:
        raise ValueError("Select a role found in this job description.")
    if len(roles) == 1:
        selected_role = roles[0]
    elif len(roles) > 1 and not selected_role:
        return {"roles": roles, "selected_role": None, "suggestions": [], "warnings": ["Choose one role before reviewing skills."]}
    suggestions = _suggestions(lines, positions, selected_role)
    warnings = [] if suggestions else ["No clear skills were detected. Review the document and add skills manually."]
    return {"roles": roles, "selected_role": selected_role, "suggestions": suggestions, "warnings": warnings}
