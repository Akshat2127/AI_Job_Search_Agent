import re

from backend.app.models.job import Job
from backend.app.services.profile import CANDIDATE_PROFILE

TITLE_BONUS = 25
KEYWORD_POINTS = 5
NEGATIVE_PENALTY = 25
REMOTE_BONUS = 5
HEALTHCARE_BONUS = 10


def normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def choose_resume_variant(text: str) -> str:
    if "servicenow" in text or "workflow" in text:
        return "servicenow_ba"
    if "claims" in text or "healthcare" in text or "insurance" in text:
        return "healthcare_bsa"
    if "product owner" in text or "backlog" in text:
        return "product_owner"
    if "city" in text or "county" in text or "government" in text or "public sector" in text:
        return "public_sector"
    return "healthcare_bsa"


def score_job(job: Job) -> tuple[int, str, str]:
    blob = normalize(
        " ".join([job.title, job.company, job.location or "", job.remote_type or "", job.description or ""])
    )
    score = 35
    reasons = []

    for title in CANDIDATE_PROFILE["target_titles"]:
        if title.lower() in blob:
            score += TITLE_BONUS
            reasons.append(f"title match: {title}")
            break

    hits = []
    for kw in CANDIDATE_PROFILE["high_value_keywords"]:
        if kw in blob:
            score += KEYWORD_POINTS
            hits.append(kw)
    if hits:
        reasons.append("keyword matches: " + ", ".join(hits[:8]))

    if "remote" in blob or "hybrid" in blob or "seattle" in blob or "bellevue" in blob or "bothell" in blob:
        score += REMOTE_BONUS
        reasons.append("location/remote fit")

    if any(x in blob for x in ["healthcare", "claims", "insurance", "payer"]):
        score += HEALTHCARE_BONUS
        reasons.append("domain fit")

    negatives = [kw for kw in CANDIDATE_PROFILE["negative_keywords"] if kw in blob]
    if negatives:
        score -= NEGATIVE_PENALTY * len(negatives)
        reasons.append("concerns: " + ", ".join(negatives))

    score = max(0, min(100, score))
    variant = choose_resume_variant(blob)
    return score, "; ".join(reasons) or "general match", variant
