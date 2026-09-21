"""季度（season）词表的唯一权威定义。

约定：动漫季 == 日历季度，与 Business ``SeasonUtil`` 及 indexer 存储的
MySQL ``QUARTER(air_date)`` 对齐：winter=1（1-3月）、spring=2（4-6月）、
summer=3（7-9月）、autumn=4（10-12月）。

标签（``spring|summer|autumn|winter``）只出现在 wire 契约与受控查询字段；
数字季度仅在 Agent 内部使用（RediSearch 表达式、Vector Set FILTER、
Evidence 过滤、shadow eval SQL、importer 档期扫描）。任何标签→数字/月份段
的换算都必须经过本模块，禁止在消费方内联第二份映射。
"""

from __future__ import annotations

SEASON_QUARTERS: dict[str, int] = {"winter": 1, "spring": 2, "summer": 3, "autumn": 4}


def season_month_range(season: str) -> tuple[int, int]:
    """返回该季度的起止月份（含两端），由季度号派生，与 MySQL QUARTER() 同语义。"""
    quarter = SEASON_QUARTERS[season]
    return (quarter - 1) * 3 + 1, quarter * 3
