from backend.app.models.job import Job
from backend.app.services.scoring import score_job


def test_bsa_scores_high():
    job = Job(
        company="X",
        title="Senior Business Systems Analyst",
        url="u",
        description="healthcare claims UAT requirements SQL",
    )
    score, reason, variant = score_job(job)
    assert score >= 70
    assert variant in {"healthcare_bsa", "servicenow_ba", "public_sector", "product_owner"}


def test_engineer_scores_lower():
    job = Job(company="X", title="Senior Software Engineer", url="u", description="java developer coding")
    score, _, _ = score_job(job)
    assert score < 60
