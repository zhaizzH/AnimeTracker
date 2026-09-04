"""Bangumi 条目响应的稳定规范化模型。"""

from dataclasses import dataclass
from datetime import datetime, timezone


MAIN_CREDIT_ROLES = frozenset({"导演", "系列构成", "脚本", "原作", "动画制作", "制片"})
ALIAS_INFOBOX_KEYS = frozenset({"别名", "中文名", "英文名"})


def infer_weekday(air_date: str | None) -> int | None:
    """从 YYYY-MM-DD 推出星期（0=周日, 1=周一 … 6=周六）。"""
    if not air_date:
        return None
    try:
        dt = datetime.strptime(air_date, "%Y-%m-%d")
        return (dt.weekday() + 1) % 7
    except (ValueError, TypeError):
        return None


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
    person_type: str = "PERSON"


@dataclass(frozen=True)
class PersonSummary:
    """Person payload embedded in a subject/persons or character/actors response."""

    bangumi_id: int
    name: str
    person_type: str
    summary: str = ""
    career: tuple[object, ...] = ()
    image_source_url: str | None = None


@dataclass(frozen=True)
class CharacterSummary:
    """Character payload embedded in a subject/characters response."""

    bangumi_id: int
    name: str
    character_type: str
    summary: str = ""
    relation: str = "MAIN"
    image_source_url: str | None = None
    actors: tuple[PersonSummary, ...] = ()


@dataclass(frozen=True)
class NormalizedSubject:
    bangumi_id: int
    name: str
    name_cn: str | None
    summary: str
    air_date: str | None
    air_weekday: int | None
    aliases: tuple[Alias, ...]
    meta_tags: tuple[str, ...]
    free_tags: tuple[Tag, ...]
    credits: tuple[Credit, ...]
    score: float | None
    rank: int | None
    rating_total: int | None
    rating_counts: dict[str, int]
    collection_total: int
    collection_counts: dict[str, int]
    image_source_url: str | None
    source_fetched_at: datetime
    eps: int | None = None
    volumes: int | None = None
    persons: tuple[PersonSummary, ...] = ()
    characters: tuple[CharacterSummary, ...] = ()


def normalize_subject(
    raw: dict,
    persons: list[dict],
    characters: list[dict] | None = None,
) -> NormalizedSubject | None:
    """将公开动画的 Bangumi 原始响应规范化；其它条目不进入导入流程。"""
    if raw.get("type") != 2 or raw.get("nsfw"):
        return None

    rating = raw.get("rating") or {}
    collection = raw.get("collection") or {}
    images = raw.get("images") or {}
    air_date = _optional_text(raw.get("date"))
    eps_value = max(_int(raw.get("eps")), _int(raw.get("total_episodes"))) or None
    volumes_value = _optional_int(raw.get("volumes"))
    return NormalizedSubject(
        bangumi_id=int(raw["id"]),
        name=_text(raw.get("name")),
        name_cn=_optional_text(raw.get("name_cn")),
        summary=_text(raw.get("summary")),
        air_date=air_date,
        air_weekday=infer_weekday(air_date),
        aliases=_aliases(raw.get("infobox") or []),
        meta_tags=_meta_tags(raw.get("meta_tags") or []),
        free_tags=_free_tags(raw.get("tags") or []),
        credits=_credits(persons),
        score=_optional_float(rating.get("score")),
        rank=_optional_int(rating.get("rank")),
        rating_total=_optional_int(rating.get("total")),
        rating_counts=_counts(rating.get("count") or {}),
        collection_total=_int(collection.get("collect")),
        collection_counts=_counts(collection),
        image_source_url=_optional_text(images.get("large")),
        source_fetched_at=datetime.now(timezone.utc),
        eps=eps_value,
        volumes=volumes_value,
        persons=_person_summaries(persons),
        characters=_character_summaries(characters or []),
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
    seen: set[tuple[int, str]] = set()
    for entry in persons:
        role = _text(entry.get("relation"))
        person = entry.get("person") or {}
        person_id = _optional_int(person.get("id"))
        name = _text(person.get("name"))
        # Bangumi person.type: 1=个人, 2=公司, 3=组合
        raw_type = _int(person.get("type")) or 1
        person_type = "ORGANIZATION" if raw_type in (2, 3) else "PERSON"
        # The subject/persons endpoint is the authoritative credit list. Keep every
        # non-empty role (not only the six UI "main" roles), otherwise roles such
        # as 製作, 音乐 and 摄影 disappear before they can be audited or searched.
        key = (person_id, role)
        if person_id is not None and name and role and key not in seen:
            seen.add(key)
            credits.append(Credit(person_id=person_id, name=name, role=role, person_type=person_type))
    return tuple(credits)


def _person_summaries(persons: list[dict]) -> tuple[PersonSummary, ...]:
    result: list[PersonSummary] = []
    seen: set[int] = set()
    for entry in persons or []:
        person = entry.get("person") if isinstance(entry, dict) else None
        if not isinstance(person, dict):
            # Be tolerant of callers passing a bare Person payload.
            person = entry if isinstance(entry, dict) else {}
        person_id = _optional_int(person.get("id"))
        name = _text(person.get("name"))
        if person_id is None or not name or person_id in seen:
            continue
        seen.add(person_id)
        result.append(_normalize_person(person))
    return tuple(result)


def _normalize_person(person: dict) -> PersonSummary:
    raw_type = _int(person.get("type"))
    person_type = {1: "PERSON", 2: "COMPANY", 3: "GROUP"}.get(raw_type, "PERSON")
    career = person.get("career")
    if isinstance(career, list):
        career_value = tuple(career)
    elif career is None:
        career_value = ()
    else:
        career_value = (career,)
    images = person.get("images") or {}
    return PersonSummary(
        bangumi_id=int(person["id"]),
        name=_text(person.get("name")),
        person_type=person_type,
        summary=_text(person.get("summary")),
        career=career_value,
        image_source_url=_optional_text(images.get("large")),
    )


def _character_summaries(characters: list[dict]) -> tuple[CharacterSummary, ...]:
    result: list[CharacterSummary] = []
    seen: set[int] = set()
    for item in characters or []:
        if not isinstance(item, dict):
            continue
        character = item
        character_id = _optional_int(character.get("id"))
        name = _text(character.get("name"))
        if character_id is None or not name or character_id in seen:
            continue
        seen.add(character_id)
        raw_type = _int(character.get("type"))
        character_type = "ORGANIZATION" if raw_type == 4 else "CHARACTER"
        images = character.get("images") or {}
        actors: list[PersonSummary] = []
        actor_seen: set[int] = set()
        for actor in character.get("actors") or []:
            if not isinstance(actor, dict):
                continue
            actor_id = _optional_int(actor.get("id"))
            if actor_id is None or actor_id in actor_seen or not _text(actor.get("name")):
                continue
            actor_seen.add(actor_id)
            actors.append(_normalize_person(actor))
        result.append(
            CharacterSummary(
                bangumi_id=int(character_id),
                name=name,
                character_type=character_type,
                summary=_text(character.get("summary")),
                relation=_normalize_character_relation(character.get("relation")),
                image_source_url=_optional_text(images.get("large")),
                actors=tuple(actors),
            )
        )
    return tuple(result)


def _normalize_character_relation(value: object) -> str:
    raw = _text(value)
    normalized = {
        "主角": "MAIN",
        "主要角色": "MAIN",
        "MAIN": "MAIN",
        "配角": "SUPPORTING",
        "SUPPORTING": "SUPPORTING",
        "客串": "GUEST",
        "GUEST": "GUEST",
    }.get(raw, raw)
    # Keep unknown upstream relation labels for audit, while respecting the schema
    # column's size. Empty labels are represented by the safe default.
    return (normalized or "MAIN")[:32]


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


def _optional_float(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
