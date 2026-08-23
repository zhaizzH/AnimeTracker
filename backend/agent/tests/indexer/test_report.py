from __future__ import annotations

from indexer.report import build_capacity_report


def test_report_blocks_when_projection_exceeds_sixty_percent():
    """若容量投影忽略 60% 门槛，500 条样本会放行无法安全容纳全量索引的 Redis。"""
    report = build_capacity_report(
        sample_bytes=40_000_000,
        sample_count=500,
        catalog_count=20_000,
        redis_used_memory=123,
        available_bytes=2_000_000_000,
    )

    assert report.bytes_per_document == 80_000
    assert report.projected_total_bytes == 1_600_000_000
    assert report.utilization == 0.8
    assert report.allowed is False


def test_report_allows_projection_at_or_below_sixty_percent():
    """若门槛错误地拒绝临界安全容量，计划中的小规格部署无法被准确评估。"""
    report = build_capacity_report(
        sample_bytes=60_000,
        sample_count=1,
        catalog_count=20_000,
        redis_used_memory=10,
        available_bytes=2_000_000_000,
    )

    assert report.projected_total_bytes == 1_200_000_000
    assert report.allowed is True
