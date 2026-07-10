from dataclasses import dataclass
import requests

@dataclass
class ExternalJob:
    company: str
    title: str
    location: str | None
    url: str
    source: str
    description: str | None = None

class LeverConnector:
    def fetch(self, company_slug: str) -> list[ExternalJob]:
        url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        jobs = []
        for item in resp.json():
            jobs.append(ExternalJob(company=company_slug, title=item.get("text", ""), location=(item.get("categories") or {}).get("location"), url=item.get("hostedUrl", ""), source="lever", description=item.get("descriptionPlain")))
        return jobs

class GreenhouseConnector:
    def fetch(self, board_token: str) -> list[ExternalJob]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        jobs = []
        for item in resp.json().get("jobs", []):
            loc = (item.get("location") or {}).get("name")
            jobs.append(ExternalJob(company=board_token, title=item.get("title", ""), location=loc, url=item.get("absolute_url", ""), source="greenhouse", description=item.get("content")))
        return jobs
