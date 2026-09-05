"""MySQL active-release pointer for RAG shadow versions."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import text


class MySqlReleaseStore:
    """Small transactional adapter used by the gate and shadow manager.

    Redis remains data-plane storage.  This adapter is the only component
    allowed to change the published index version.
    """

    def __init__(self, session_factory: Callable[[], Any]):
        self._session_factory = session_factory

    def active_version(self) -> str | None:
        with self._session_factory() as session:
            row = session.execute(
                text(
                    "SELECT index_version FROM search_index_release "
                    "WHERE status='ACTIVE' AND active_slot=1 "
                    "ORDER BY activated_at DESC, index_version DESC LIMIT 1"
                )
            ).mappings().first()
        return str(row["index_version"]) if row else None

    def activate(self, index_version: str) -> None:
        if not isinstance(index_version, str) or not index_version or ":" in index_version or any(char.isspace() for char in index_version):
            raise ValueError("index_version 无效")
        now = datetime.now()
        with self._session_factory() as session:
            with session.begin():
                target = session.execute(
                    text(
                        "SELECT id, status FROM search_index_release "
                        "WHERE index_version=:version FOR UPDATE"
                    ),
                    {"version": index_version},
                ).mappings().first()
                if target is None:
                    raise ValueError(f"release 不存在: {index_version}")
                if str(target["status"]) == "ACTIVE":
                    return
                session.execute(
                    text(
                        "UPDATE search_index_release SET status='RETIRED', retired_at=:now, updated_at=:now "
                        "WHERE status='ACTIVE'"
                    ),
                    {"now": now},
                )
                session.execute(
                    text(
                        "UPDATE search_index_release SET status='ACTIVE', activated_at=:now, "
                        "retired_at=NULL, updated_at=:now WHERE id=:id"
                    ),
                    {"id": int(target["id"]), "now": now},
                )
