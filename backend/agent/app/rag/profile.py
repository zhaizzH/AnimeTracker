from __future__ import annotations

import hashlib
import json

from app.rag.schemas import SubjectProfile, SubjectProfileSource


PROFILE_SCHEMA_VERSION = "subject-profile-v1"
_EMBEDDING_PROVIDER = "dashscope"


def build_subject_profile(
    source: SubjectProfileSource,
    model: str,
    dimensions: int,
) -> SubjectProfile:
    """将不会频繁变化的条目资料编排成可重现的向量文本。"""
    text = "\n".join(
        filter(
            None,
            (
                f"标题：{source.title}",
                f"别名：{'、'.join(source.aliases)}" if source.aliases else "",
                f"简介：{source.summary}" if source.summary else "",
                f"官方标签：{'、'.join(source.meta_tags)}" if source.meta_tags else "",
                f"可信标签：{'、'.join(source.trusted_tags)}" if source.trusted_tags else "",
                f"主创与制作：{'、'.join(source.credits)}" if source.credits else "",
                f"系列关系：{'、'.join(source.relations)}" if source.relations else "",
            ),
        )
    )
    envelope = {
        "schema": PROFILE_SCHEMA_VERSION,
        "provider": _EMBEDDING_PROVIDER,
        "model": model,
        "dimensions": dimensions,
        "text": text,
    }
    content_hash = hashlib.sha256(
        json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return SubjectProfile(
        text=text,
        content_hash=content_hash,
        schema_version=PROFILE_SCHEMA_VERSION,
    )
