"""统一 job 表 payload_json 的编解码。

差异元数据（embedding 元组、profile 版本、source_id、checkpoint、source_hash）
统一存入 job.payload_json；查询条件（type/entity_kind/entity_id/index_version/content_hash/status）
保留为列。
"""

from __future__ import annotations

import json

def encode(payload: dict | None) -> str:
    return json.dumps(payload or {}, ensure_ascii=False, default=str)


def decode(value: object) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", "replace")
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
