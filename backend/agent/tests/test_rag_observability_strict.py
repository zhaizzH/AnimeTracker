from __future__ import annotations

import json
import logging

from app.core.observability import log_event


def test_rag_event_does_not_inherit_general_observability_fields(caplog):
    with caplog.at_level(logging.INFO, logger="app.core.observability"):
        log_event(
            "rag.index.completed",
            indexVersion="v1",
            candidateCount=3,
            provider="vendor",
            model="secret-model",
            sessionHash="hashed-session",
            toolCount=9,
            success=True,
        )

    payload = json.loads(caplog.records[-1].message)
    assert payload == {
        "service": "animetracker-agent",
        "event": "rag.index.completed",
        "indexVersion": "v1",
        "candidateCount": 3,
        "success": True,
    }
