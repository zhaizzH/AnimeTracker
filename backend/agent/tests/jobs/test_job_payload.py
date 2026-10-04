"""`jobs/job_payload.py` 的编解码契约。

`job.payload_json` 是三处仓储（backfill / indexer / search）共用的差异元数据载体，
encode/decode 必须对 MySQL JSON 列可能返回的每种形态都给出可用结果——读写一旦不
对称，claim 时 `profile_version` / `source_id` 会静默变成默认值。
"""

from __future__ import annotations

import pytest

from jobs.job_payload import decode, encode


class TestEncode:
    def test_none_encodes_to_empty_object(self):
        assert encode(None) == "{}"

    def test_empty_dict_encodes_to_empty_object(self):
        assert encode({}) == "{}"

    def test_roundtrip_preserves_values(self):
        payload = {"source_id": 100, "profile_version": "v1", "embedding_dimensions": 1024}
        assert decode(encode(payload)) == payload

    def test_non_ascii_is_not_escaped(self):
        """ensure_ascii=False：中文不该被转成 \\uXXXX（payload 可读性与体积）。"""
        assert "制作" in encode({"role": "制作"})

    def test_unserializable_value_falls_back_to_str(self):
        """default=str 兜底：datetime 等不可 JSON 化的值不应让入队整体失败。"""
        from datetime import datetime

        encoded = encode({"at": datetime(2026, 10, 4, 12, 0, 0)})
        assert decode(encoded)["at"].startswith("2026-10-04")


class TestDecode:
    def test_none_returns_empty_dict(self):
        assert decode(None) == {}

    def test_dict_passes_through(self):
        """MySQL JSON 列在部分驱动配置下直接返回 dict。"""
        payload = {"source_id": 7}
        assert decode(payload) == payload

    def test_bytes_are_decoded(self):
        """decode_responses=False 的驱动会返回 bytes。"""
        assert decode(b'{"source_id": 7}') == {"source_id": 7}

    def test_invalid_json_returns_empty_dict(self):
        assert decode("not json{") == {}

    def test_non_dict_json_returns_empty_dict(self):
        """payload 列只允许对象；数组/标量一律视作空，避免下游 .get 抛 AttributeError。"""
        assert decode("[1, 2, 3]") == {}
        assert decode("42") == {}
        assert decode('"text"') == {}
        assert decode("null") == {}

    def test_binary_bytes_do_not_raise(self):
        assert decode(b"\xff\xfe") == {}

    def test_empty_string_returns_empty_dict(self):
        """旧行/未写入时列为空串而非 NULL。"""
        assert decode("") == {}


@pytest.mark.parametrize(
    "source_id_payload",
    [
        {"source_id": 0},
        {"source_id": 12345},
    ],
)
def test_missing_key_defaults_are_caller_side(source_id_payload):
    """decode 不补默认值——缺字段由调用方的 `payload.get(...) or 0` 兜底。

    这条锁定契约边界，防止有人往 decode 里塞业务默认值。
    """
    assert decode(encode(source_id_payload)) == source_id_payload
