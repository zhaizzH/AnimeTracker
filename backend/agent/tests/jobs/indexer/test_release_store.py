from unittest.mock import MagicMock

import pytest

from app.adapters.mysql.release_store import MySqlReleaseStore


def _session(*rows):
    session = MagicMock()
    result = MagicMock()
    result.mappings.return_value.first.side_effect = list(rows)
    session.execute.return_value = result
    session.__enter__.return_value = session
    session.begin.return_value.__enter__.return_value = session
    return session


def test_active_version_reads_mysql_release_pointer():
    session = _session({"index_version": "v2026-09"})
    store = MySqlReleaseStore(lambda: session)

    assert store.active_version() == "v2026-09"
    session.execute.assert_called_once()


def test_activate_retires_old_release_before_target():
    session = _session({"id": 7, "status": "BUILDING"})
    store = MySqlReleaseStore(lambda: session)

    store.activate("v2026-09")

    assert session.execute.call_count == 3
    assert "status='RETIRED'" in str(session.execute.call_args_list[1].args[0])
    assert "status='ACTIVE'" in str(session.execute.call_args_list[2].args[0])


def test_activate_rejects_untrusted_version_without_opening_db():
    session = MagicMock()
    store = MySqlReleaseStore(lambda: session)

    with pytest.raises(ValueError):
        store.activate("v1:unsafe")

    session.execute.assert_not_called()
