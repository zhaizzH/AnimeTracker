from __future__ import annotations

from datetime import datetime

import pytest

from importer.normalize import Alias, Credit, Tag, normalize_subject


@pytest.mark.parametrize(
    "raw",
    [{"id": 1, "type": 1, "nsfw": False}, {"id": 2, "type": 2, "nsfw": True}],
)
def test_normalize_rejects_non_public_anime(raw):
    assert normalize_subject(raw, []) is None


def test_normalize_separates_aliases_tags_and_whitelisted_credits():
    raw = {
        "id": 42,
        "type": 2,
        "nsfw": False,
        "name": "Original title",
        "name_cn": "中文标题",
        "summary": "Summary",
        "infobox": [
            {"key": "别名", "value": "Original title / Alt title"},
            {"key": "中文名", "value": "中文标题"},
            {"key": "英文名", "value": "English title"},
        ],
        "meta_tags": ["动画", " 科幻 ", ""],
        "tags": [{"name": "科幻", "count": 9}, {"name": "  ", "count": 999}],
        "rating": {"total": 100, "count": {"10": 80}},
        "collection": {"wish": 1, "collect": 2},
        "images": {"large": "https://example.test/cover.jpg"},
    }
    persons = [
        {"relation": "导演", "person": {"id": 7, "name": "Director"}},
        {"relation": "配角", "person": {"id": 8, "name": "Ignored"}},
    ]

    subject = normalize_subject(raw, persons)

    assert subject is not None
    assert subject.aliases == (
        Alias(name="Original title", kind="别名"),
        Alias(name="Alt title", kind="别名"),
        Alias(name="中文标题", kind="中文名"),
        Alias(name="English title", kind="英文名"),
    )
    assert subject.meta_tags == ("动画", "科幻")
    assert subject.free_tags == (Tag(name="科幻", count=9),)
    assert subject.credits == (Credit(person_id=7, name="Director", role="导演"),)
    assert subject.rating_total == 100
    assert subject.rating_counts == {"10": 80}
    assert subject.collection_counts == {"wish": 1, "collect": 2}
    assert subject.image_source_url == "https://example.test/cover.jpg"
    assert isinstance(subject.source_fetched_at, datetime)
