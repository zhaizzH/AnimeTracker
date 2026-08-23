"""Bangumi 条目响应的稳定规范化模型。"""

from dataclasses import dataclass
from datetime import datetime, timezone


MAIN_CREDIT_ROLES = frozenset({"导演", "系列构成", "脚本", "原作", "动画制作", "制片"})
ALIAS_INFOBOX_KEYS = frozenset({"别名", "中文名", "英文名"})


@dataclass(frozen=True)
class Alias:
    name: str
    kind: str


@dataclass(frozen=True)
class Tag:
    name: str
    count: int


@dataclass(frozen=True)
class Credit:
    person_id: int
    name: str
    role: str


@dataclass(frozen=True)
class NormalizedSubject:
    bangumi_id: int
    name: str
    name_cn: str | None
    summary: str
    aliases: tuple[Alias, ...]
    meta_tags: tuple[str, ...]
    free_tags: tuple[Tag, ...]
    credits: tuple[Credit, ...]
    rating_total: int | None
    rating_counts: dict[str, int]
    collection_counts: dict[str, int]
    image_source_url: str | None
    source_fetched_at: datetime


def normalize_subject(raw: dict, persons: list[dict]) -> NormalizedSubject | None:
    """将公开动画的 Bangumi 原始响应规范化；其它条目不进入导入流程。"""
    if raw.get("type") != 2 or raw.get("nsfw"):
        return None

    rating = raw.get("rating") or {}
    collection = raw.get("collection") or {}
    images = raw.get("images") or {}
    return NormalizedSubject(
        bangumi_id=int(raw["id"]),
        name=_text(raw.get("name")),
        name_cn=_optional_text(raw.get("name_cn")),
        summary=_text(raw.get("summary")),
        aliases=_aliases(raw.get("infobox") or []),
        meta_tags=_meta_tags(raw.get("meta_tags") or []),
        free_tags=_free_tags(raw.get("tags") or []),
        credits=_credits(persons),
        rating_total=_optional_int(rating.get("total")),
        rating_counts=_counts(rating.get("count") or {}),
        collection_counts=_counts(collection),
        image_source_url=_optional_text(images.get("large")),
        source_fetched_at=datetime.now(timezone.utc),
    )


def _aliases(infobox: list[dict]) -> tuple[Alias, ...]:
    aliases = []
    seen = set()
    for field in infobox:
        kind = _text(field.get("key"))
        if kind not in ALIAS_INFOBOX_KEYS:
            continue
        for value in _split_aliases(field.get("value")):
            if value not in seen:
                seen.add(value)
                aliases.append(Alias(name=value, kind=kind))
    return tuple(aliases)


def _split_aliases(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(item for part in value for item in _split_aliases(part))
    return tuple(part.strip() for part in _text(value).split("/") if part.strip())


def _meta_tags(tags: list[object]) -> tuple[str, ...]:
    values = []
    seen = set()
    for tag in tags:
        value = _text(tag.get("name") if isinstance(tag, dict) else tag)
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return tuple(values)


def _free_tags(tags: list[dict]) -> tuple[Tag, ...]:
    return tuple(
        Tag(name=name, count=_int(tag.get("count")))
        for tag in tags
        if (name := _text(tag.get("name")))
    )


def _credits(persons: list[dict]) -> tuple[Credit, ...]:
    credits = []
    for entry in persons:
        role = _text(entry.get("relation"))
        person = entry.get("person") or {}
        person_id = _optional_int(person.get("id"))
        name = _text(person.get("name"))
        if role in MAIN_CREDIT_ROLES and person_id is not None and name:
            credits.append(Credit(person_id=person_id, name=name, role=role))
    return tuple(credits)


def _counts(raw: dict) -> dict[str, int]:
    return {str(key): _int(value) for key, value in raw.items()}


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _optional_text(value: object) -> str | None:
    return _text(value) or None


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _optional_int(value: object) -> int | None:
    return _int(value) if value is not None else None
