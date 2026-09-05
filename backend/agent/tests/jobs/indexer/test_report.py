import json

import pytest

from jobs.indexer.report import build_capacity_report


def test_capacity_report_projects_document_memory_and_gate():
    report = build_capacity_report(
        sample_bytes=10_000,
        sample_count=100,
        catalog_count=500,
        redis_used_memory=2_000,
        available_bytes=1_000_000,
    )

    assert report.bytes_per_document == 100
    assert report.projected_total_bytes == 50_000
    assert report.utilization == pytest.approx(0.05)
    assert report.allowed is True


def test_capacity_report_rejects_empty_sample():
    report = build_capacity_report(
        sample_bytes=0,
        sample_count=0,
        catalog_count=500,
        redis_used_memory=2_000,
        available_bytes=1_000_000,
    )

    assert report.allowed is False
    assert report.projected_total_bytes == 0


def test_capacity_report_json_is_machine_readable():
    report = build_capacity_report(
        sample_bytes=1_000,
        sample_count=10,
        catalog_count=20,
        redis_used_memory=100,
        available_bytes=10_000,
    )
    payload = json.loads(json.dumps(report.as_dict(), ensure_ascii=False))
    assert payload["allowed"] is True
    assert payload["projected_total_bytes"] == 2_000
