from __future__ import annotations

import json
import logging

from app.core.observability import log_event


def test_rag_event_drops_sensitive_payloads(caplog):
    with caplog.at_level(logging.INFO, logger="app.core.observability"):
        log_event(
            "rag.retrieval.completed",
            candidateCount=12,
            query="secret text",
            profile="user profile",
            vector=[1.0],
            jwt="header.payload.signature",
            apiKey="secret",
            favorites=[1, 2],
            vendorResponse={"raw": "secret"},
            success=True,
        )

    payload = json.loads(caplog.records[-1].message)
    assert payload == {
        "service": "animetracker-agent",
        "event": "rag.retrieval.completed",
        "candidateCount": 12,
        "success": True,
    }


def test_unknown_rag_event_is_not_emitted(caplog):
    with caplog.at_level(logging.INFO, logger="app.core.observability"):
        log_event("rag.query.debug", candidateCount=12)

    assert not caplog.records
