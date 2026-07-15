from dataclasses import dataclass
from typing import Protocol

import requests


@dataclass
class ExternalJob:
    external_id: str
    company: str
    title: str
    location: str | None
    url: str
    source: str
    description: str | None = None
    raw_payload: dict | None = None


class JobConnector(Protocol):
    def fetch(self, source_key: str) -> list[ExternalJob]: ...


class LeverConnector:
    def fetch(self, company_slug: str) -> list[ExternalJob]:
        url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        jobs = []
        for item in resp.json():
            jobs.append(
                ExternalJob(
                    external_id=str(item.get("id") or item.get("hostedUrl") or ""),
                    company=company_slug,
                    title=item.get("text", ""),
                    location=(item.get("categories") or {}).get("location"),
                    url=item.get("hostedUrl", ""),
                    source="lever",
                    description=item.get("descriptionPlain"),
                    raw_payload=item,
                )
            )
        return jobs


class GreenhouseConnector:
    def fetch(self, board_token: str) -> list[ExternalJob]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        jobs = []
        for item in resp.json().get("jobs", []):
            loc = (item.get("location") or {}).get("name")
            jobs.append(
                ExternalJob(
                    external_id=str(item.get("id") or item.get("absolute_url") or ""),
                    company=board_token,
                    title=item.get("title", ""),
                    location=loc,
                    url=item.get("absolute_url", ""),
                    source="greenhouse",
                    description=item.get("content"),
                    raw_payload=item,
                )
            )
        return jobs
