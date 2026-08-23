from __future__ import annotations

from app.rag.profile import PROFILE_SCHEMA_VERSION, build_subject_profile
from app.rag.schemas import SubjectProfileSource


MODEL = "text-embedding-v4"
SOURCE = SubjectProfileSource(
    title="葬送的芙莉莲",
    aliases=("Frieren", "Frieren: Beyond Journey's End"),
    summary="精灵魔法使踏上回望旅程。",
    meta_tags=("TV", "奇幻"),
    trusted_tags=("治愈", "冒险"),
    credits=("导演：斋藤圭一郎",),
    relations=("续作：葬送的芙莉莲 第二季",),
    score=8.9,
    air_date="2023-09-29",
)


def test_profile_text_contains_only_stable_subject_fields():
    """动态评分与放送信息不应进入向量档案。"""
    profile = build_subject_profile(SOURCE, MODEL, 1024)

    assert profile.text == "\n".join(
        (
            "标题：葬送的芙莉莲",
            "别名：Frieren、Frieren: Beyond Journey's End",
            "简介：精灵魔法使踏上回望旅程。",
            "官方标签：TV、奇幻",
            "可信标签：治愈、冒险",
            "主创与制作：导演：斋藤圭一郎",
            "系列关系：续作：葬送的芙莉莲 第二季",
        )
    )
    assert "8.9" not in profile.text
    assert "2023-09-29" not in profile.text


def test_profile_hash_ignores_dynamic_score_and_air_fields():
    """动态字段变化不得触发向量重建。"""
    first = build_subject_profile(
        SOURCE.model_copy(update={"score": 8.1, "air_date": "2023-10-06"}),
        MODEL,
        1024,
    )
    second = build_subject_profile(
        SOURCE.model_copy(update={"score": 8.8, "air_date": "2024-01-01"}),
        MODEL,
        1024,
    )

    assert first.content_hash == second.content_hash


def test_profile_hash_changes_for_embedding_contract_changes():
    """模型或维度变化必须使既有向量失效。"""
    baseline = build_subject_profile(SOURCE, MODEL, 1024)

    assert baseline.schema_version == PROFILE_SCHEMA_VERSION
    assert baseline.content_hash != build_subject_profile(SOURCE, "another-model", 1024).content_hash
    assert baseline.content_hash != build_subject_profile(SOURCE, MODEL, 512).content_hash
