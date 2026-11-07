from dataclasses import dataclass, field


@dataclass(frozen=True)
class Evidence:
    id: str
    source: str
    location: str
    text: str


@dataclass
class JobDescription:
    id: str
    title: str
    required: list[str]
    preferred: list[str]
    evidence: list[Evidence]
    selected_role: str | None = None
    extractor_version: str | None = None
    reviewed_at: str | None = None
    reviewed_requirements: list[dict] = field(default_factory=list)
    department: str = "Unassigned"


@dataclass
class Candidate:
    id: str
    name: str
    evidence: list[Evidence]
    tags: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    candidate_id: str
    candidate_name: str
    score: int
    required_percent: int
    preferred_percent: int
    similarity_percent: int
    matched_required: list[str]
    missing_required: list[str]
    matched_preferred: list[str]
    missing_preferred: list[str]
    evidence: dict[str, Evidence] = field(default_factory=dict)


@dataclass
class Workspace:
    jds: list[JobDescription]
    candidates: list[Candidate]
    selected_jd_id: str
    recruitment: list[dict[str, str]] = field(default_factory=list)
    drafts: list[dict[str, str]] = field(default_factory=list)
    revision: int = 0

    def active_jd(self) -> JobDescription:
        return next(jd for jd in self.jds if jd.id == self.selected_jd_id)


def workspace_from_dict(data: dict) -> Workspace:
    jds = [
        JobDescription(item["id"], item["title"], item["required"], item["preferred"],
                       [Evidence(**evidence) for evidence in item["evidence"]],
                       item.get("selected_role"), item.get("extractor_version"),
                       item.get("reviewed_at"), item.get("reviewed_requirements", []), item.get("department", "Unassigned"))
        for item in data["jds"]
    ]
    candidates = [
        Candidate(item["id"], item["name"], [Evidence(**evidence) for evidence in item["evidence"]], item.get("tags", []))
        for item in data["candidates"]
    ]
    return Workspace(jds, candidates, data["selected_jd_id"], data.get("recruitment", []), data.get("drafts", []), data.get("revision", 0))
