"""Regression tests for the MySQL lexical and Vector Set boundaries."""

from __future__ import annotations

import json

from app.entities.enums import EntityKind
from app.rag.retrieval import RagRetrievalService
from app.rag.schemas import SubjectProfile
from jobs.indexer.entity_index import EntityIndexDocument, RedisEntityIndex


def test_business_lexical_candidates_are_normalized_for_rrf():
    candidates = RagRetrievalService._as_candidates(
        {
            "indexVersion": "v2026-09",
            "candidates": [
                {
                    "subjectId": 42,
                    "name": "Cowboy Bebop",
                    "nameCn": "星际牛仔",
                    "lexicalScore": 3.25,
                }
            ],
        },
        "lexical",
    )

    assert len(candidates) == 1
    assert candidates[0].subject_id == 42
    assert candidates[0].retrieval_score == 3.25
    assert candidates[0].title == "星际牛仔"


def test_generic_subject_vector_writes_filter_metadata():
    class Redis:
        def __init__(self):
            self.commands = []

        def execute_command(self, *args):
            self.commands.append(args)
            return 1

    redis = Redis()
    index = RedisEntityIndex(redis)
    profile = SubjectProfile(
        text="测试动画",
        content_hash="a" * 64,
        schema_version="subject-profile-v1",
    )
    index.write(
        EntityIndexDocument(
            entity_kind=EntityKind.SUBJECT,
            entity_id=42,
            index_version="v2026-09",
            profile=profile,
            vector=[0.0] * 1024,
            name="测试动画",
            type=2,
            nsfw=False,
            year=2026,
            quarter=3,
            score=8.5,
            rating_total=100,
            collection_total=200,
            air_status="finished",
        )
    )

    command = redis.commands[0]
    attributes = json.loads(command[command.index("SETATTR") + 1])
    assert attributes["type"] == 2
    assert attributes["nsfw"] is False
    assert attributes["year"] == 2026
    assert attributes["quarter"] == 3
    assert attributes["air_status"] == "finished"
