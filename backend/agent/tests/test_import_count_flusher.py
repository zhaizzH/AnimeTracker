import sys
import time
from pathlib import Path

# importer/main.py 用平铺 `from client import ...`（脚本式运行），需把 importer 目录挂进 path
_IMPORTER_DIR = str(Path(__file__).resolve().parents[1] / "importer")
sys.path.insert(0, _IMPORTER_DIR)
from importer import main as importer_main
sys.path.remove(_IMPORTER_DIR)


def test_count_flusher_writes_subject_count_and_stops(monkeypatch):
    executed = []

    class FakeSession:
        def __init__(self, engine):
            pass

        def execute(self, stmt, params):
            executed.append((stmt, params))

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(importer_main, "Session", FakeSession)
    monkeypatch.setattr(importer_main, "_done_count", 7)

    stop = importer_main._start_count_flusher(record_id=123, engine=object(), every=0.02)
    time.sleep(0.08)
    stop.set()

    assert executed, "flusher 应至少向 import_record 写入一次 subject_count"
    stmt, params = executed[-1]
    assert "subject_count" in str(stmt)
    assert params["id"] == 123 and params["n"] == 7
