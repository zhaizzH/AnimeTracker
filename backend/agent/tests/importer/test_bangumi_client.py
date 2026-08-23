from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from importer.client import BangumiClient


class FakeBangumiClient(BangumiClient):
    def __init__(self, pages: dict[int, dict]):
        self.pages = pages
        self.requests: list[tuple[str, dict | None]] = []

    def browse_subjects(self, type=2, year=None, month=None, offset=0, limit=25):
        self.requests.append(("subjects", {"type": type, "offset": offset, "limit": limit}))
        return self.pages[offset]

    def get_episodes(self, subject_id, type=None, limit=200, offset=0):
        self.requests.append(("episodes", {"subject_id": subject_id, "offset": offset, "limit": limit}))
        return self.pages[offset]


def test_iter_subject_ids_reads_every_page_once():
    client = FakeBangumiClient(
        {
            0: {"data": [{"id": 3}, {"id": 1}], "total": 3},
            2: {"data": [{"id": 3}, {"id": 2}], "total": 3},
        }
    )

    assert list(client.iter_subject_ids(limit=2)) == [3, 1, 2]
    assert client.requests == [
        ("subjects", {"type": 2, "offset": 0, "limit": 2}),
        ("subjects", {"type": 2, "offset": 2, "limit": 2}),
    ]


def test_iter_subject_ids_stops_on_empty_page_when_total_changes():
    client = FakeBangumiClient(
        {
            0: {"data": [{"id": 1}, {"id": 2}], "total": 10},
            2: {"data": [], "total": 10},
        }
    )

    assert list(client.iter_subject_ids(limit=2)) == [1, 2]
    assert [request[1]["offset"] for request in client.requests] == [0, 2]


def test_get_all_episodes_reads_pages_larger_than_default_limit():
    client = FakeBangumiClient(
        {
            0: {"data": [{"id": n} for n in range(1, 201)], "total": 201},
            200: {"data": [{"id": 201}], "total": 201},
        }
    )

    assert client.get_all_episodes(42) == [{"id": n} for n in range(1, 202)]
    assert [request[1]["offset"] for request in client.requests] == [0, 200]


def test_get_subject_persons_uses_subject_persons_endpoint():
    client = BangumiClient(base_url="https://example.test")
    client._request = Mock(return_value=[{"relation": "导演"}])

    assert client.get_subject_persons(42) == [{"relation": "导演"}]
    client._request.assert_called_once_with("GET", "/v0/subjects/42/persons")


@pytest.mark.parametrize(
    ("status_code", "expected_calls", "error_type"),
    [(401, 1, requests.exceptions.HTTPError), (429, 3, RuntimeError), (503, 3, RuntimeError)],
)
def test_request_keeps_existing_retry_policy(monkeypatch, status_code, expected_calls, error_type):
    client = BangumiClient(base_url="https://example.test")
    response = Mock(status_code=status_code, headers={"Retry-After": "0"})
    error = requests.exceptions.HTTPError(response=response)
    response.raise_for_status.side_effect = error
    client._session.request = Mock(return_value=response)
    monkeypatch.setattr("importer.client.time.sleep", lambda _: None)

    with pytest.raises(error_type):
        client.get_subject(42)

    assert client._session.request.call_count == expected_calls
