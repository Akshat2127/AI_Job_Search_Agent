import re

from backend.app.schemas.job import JobCreate

JOB_URL_RE = re.compile(r"https?://\S+")


def parse_job_alert_text(text: str, source: str = "gmail_alert") -> list[JobCreate]:
    """Lightweight parser for alert emails. Real Gmail API integration will feed email bodies here."""
    jobs = []
    for line in text.splitlines():
        if "business analyst" in line.lower() or "systems analyst" in line.lower() or "product owner" in line.lower():
            urls = JOB_URL_RE.findall(line)
            jobs.append(
                JobCreate(
                    company="Unknown", title=line[:120], url=urls[0] if urls else "", source=source, description=line
                )
            )
    return jobs
