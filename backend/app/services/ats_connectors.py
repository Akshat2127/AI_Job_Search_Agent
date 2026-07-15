import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import requests

SOURCE_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$")
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


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


class HttpResponse(Protocol):
    status_code: int
    headers: dict[str, str]

    def json(self) -> Any: ...


class HttpClient(Protocol):
    def get(self, url: str, *, params: dict[str, Any], timeout: tuple[float, float]) -> HttpResponse: ...


class ConnectorError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class BaseConnector:
    def __init__(
        self,
        client: HttpClient | None = None,
        *,
        timeout: tuple[float, float] = (3.05, 15.0),
        max_retries: int = 2,
        min_interval_seconds: float = 0.1,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.client = client or requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.min_interval_seconds = min_interval_seconds
        self.sleep = sleep
        self.monotonic = monotonic
        self._last_request_at: float | None = None

    def _validate_source_key(self, source_key: str) -> str:
        if not SOURCE_KEY_PATTERN.fullmatch(source_key):
            raise ConnectorError("invalid_source_key", "Source key contains unsupported characters", 422)
        return source_key

    def _rate_limit(self) -> None:
        if self._last_request_at is None:
            return
        remaining = self.min_interval_seconds - (self.monotonic() - self._last_request_at)
        if remaining > 0:
            self.sleep(remaining)

    def _get_json(self, url: str, params: dict[str, Any]) -> Any:
        for attempt in range(self.max_retries + 1):
            self._rate_limit()
            try:
                response = self.client.get(url, params=params, timeout=self.timeout)
                self._last_request_at = self.monotonic()
            except requests.Timeout as error:
                if attempt < self.max_retries:
                    self.sleep(min(2**attempt, 4))
                    continue
                raise ConnectorError("upstream_timeout", "The ATS provider timed out", 504) from error
            except requests.RequestException as error:
                raise ConnectorError("upstream_unavailable", "The ATS provider could not be reached") from error

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                retry_after = response.headers.get("Retry-After")
                delay = min(float(retry_after), 5.0) if retry_after and retry_after.isdigit() else min(2**attempt, 4)
                self.sleep(delay)
                continue
            if response.status_code == 429:
                raise ConnectorError("upstream_rate_limited", "The ATS provider rate limit was reached", 503)
            if response.status_code < 200 or response.status_code >= 300:
                raise ConnectorError("upstream_http_error", f"The ATS provider returned HTTP {response.status_code}")
            try:
                return response.json()
            except (TypeError, ValueError) as error:
                raise ConnectorError("invalid_upstream_response", "The ATS provider returned invalid JSON") from error
        raise ConnectorError("upstream_unavailable", "The ATS provider could not be reached")


class LeverConnector(BaseConnector):
    page_size = 100
    max_pages = 20

    def fetch(self, source_key: str) -> list[ExternalJob]:
        company_slug = self._validate_source_key(source_key)
        url = f"https://api.lever.co/v0/postings/{company_slug}"
        jobs: list[ExternalJob] = []
        for page in range(self.max_pages):
            payload = self._get_json(
                url,
                {"mode": "json", "skip": page * self.page_size, "limit": self.page_size},
            )
            if not isinstance(payload, list):
                raise ConnectorError("invalid_upstream_response", "Lever returned an unexpected response shape")
            for item in payload:
                if not isinstance(item, dict):
                    raise ConnectorError("invalid_upstream_response", "Lever returned an invalid job record")
                jobs.append(
                    ExternalJob(
                        external_id=str(item.get("id") or item.get("hostedUrl") or ""),
                        company=company_slug,
                        title=str(item.get("text") or ""),
                        location=(item.get("categories") or {}).get("location"),
                        url=str(item.get("hostedUrl") or ""),
                        source="lever",
                        description=item.get("descriptionPlain"),
                        raw_payload=item,
                    )
                )
            if len(payload) < self.page_size:
                return jobs
        raise ConnectorError("result_limit_exceeded", "Lever returned more than the configured job limit")


class GreenhouseConnector(BaseConnector):
    max_jobs = 5000

    def fetch(self, source_key: str) -> list[ExternalJob]:
        board_token = self._validate_source_key(source_key)
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
        payload = self._get_json(url, {"content": "true"})
        if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
            raise ConnectorError("invalid_upstream_response", "Greenhouse returned an unexpected response shape")
        items = payload["jobs"]
        if len(items) > self.max_jobs:
            raise ConnectorError("result_limit_exceeded", "Greenhouse returned more than the configured job limit")
        jobs: list[ExternalJob] = []
        for item in items:
            if not isinstance(item, dict):
                raise ConnectorError("invalid_upstream_response", "Greenhouse returned an invalid job record")
            jobs.append(
                ExternalJob(
                    external_id=str(item.get("id") or item.get("absolute_url") or ""),
                    company=board_token,
                    title=str(item.get("title") or ""),
                    location=(item.get("location") or {}).get("name"),
                    url=str(item.get("absolute_url") or ""),
                    source="greenhouse",
                    description=item.get("content"),
                    raw_payload=item,
                )
            )
        return jobs


def connector_for(provider: str) -> JobConnector:
    if provider == "greenhouse":
        return GreenhouseConnector()
    if provider == "lever":
        return LeverConnector()
    raise ConnectorError("unsupported_provider", "The connector provider is not supported", 422)
