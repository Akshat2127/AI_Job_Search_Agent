import requests

from backend.app.services.ats_connectors import ConnectorError, GreenhouseConnector, LeverConnector
from backend.app.services.ingestion import plain_text


class FakeResponse:
    def __init__(self, payload, status_code: int = 200, headers: dict[str, str] | None = None):
        self.payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[tuple[str, dict, tuple[float, float]]] = []

    def get(self, url, *, params, timeout):
        self.calls.append((url, params, timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def lever_job(job_id: str) -> dict:
    return {
        "id": job_id,
        "text": f"Engineer {job_id}",
        "hostedUrl": f"https://jobs.lever.co/example/{job_id}",
        "categories": {"location": "Remote"},
        "descriptionPlain": "Build systems",
    }


def test_lever_uses_bounded_pagination_and_injected_rate_limit():
    client = FakeClient([FakeResponse([lever_job("1"), lever_job("2")]), FakeResponse([lever_job("3")])])
    sleeps: list[float] = []
    clock_values = iter([0.0, 0.0, 0.0, 0.0])
    connector = LeverConnector(
        client,
        min_interval_seconds=0.25,
        sleep=sleeps.append,
        monotonic=lambda: next(clock_values),
    )
    connector.page_size = 2

    jobs = connector.fetch("example")

    assert [job.external_id for job in jobs] == ["1", "2", "3"]
    assert client.calls[0][0] == "https://api.lever.co/v0/postings/example"
    assert client.calls[0][1] == {"mode": "json", "skip": 0, "limit": 2}
    assert client.calls[1][1]["skip"] == 2
    assert sleeps == [0.25]


def test_connector_retries_timeout_and_retryable_status_with_bounds():
    client = FakeClient(
        [
            requests.Timeout("slow"),
            FakeResponse({}, status_code=503),
            FakeResponse({"jobs": []}),
        ]
    )
    sleeps: list[float] = []
    connector = GreenhouseConnector(client, max_retries=2, min_interval_seconds=0, sleep=sleeps.append)

    assert connector.fetch("example") == []
    assert len(client.calls) == 3
    assert sleeps == [1, 2]


def test_connector_rejects_unsafe_source_key_and_malformed_response():
    client = FakeClient([FakeResponse({"unexpected": []})])
    connector = GreenhouseConnector(client, min_interval_seconds=0)

    try:
        connector.fetch("https://127.0.0.1/private")
    except ConnectorError as error:
        assert error.code == "invalid_source_key"
    else:
        raise AssertionError("unsafe source key was accepted")
    assert client.calls == []

    try:
        connector.fetch("example")
    except ConnectorError as error:
        assert error.code == "invalid_upstream_response"
    else:
        raise AssertionError("malformed response was accepted")


def test_greenhouse_entity_encoded_html_normalizes_to_plain_text():
    assert plain_text(
        "&amp;lt;p&amp;gt;Build &amp;lt;strong&amp;gt;safe&amp;lt;/strong&amp;gt; systems&amp;lt;/p&amp;gt;"
    ) == ("Build safe systems")
