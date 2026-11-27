"""真实内存 Store 跑 board：不建 SQLite，mypy 校验 StorePort。"""

from __future__ import annotations

from datetime import date
from typing import Any

from amber.app.run import board
from amber.config import Settings
from amber.domain.models import Dep, Snapshot, Task
from amber.ports import StorePort


class InMemoryStore:
    def list_tasks(self) -> list[Task]:
        return []

    def list_deps(self) -> list[Dep]:
        return []

    def list_snapshots(self) -> list[Snapshot]:
        return []

    def enqueue(self, idem_key: str, kind: str, payload: str, due_on: date) -> bool:
        return True

    def due_jobs(self, today: date) -> list[Any]:
        return []

    def finish_job(self, job_id: int, ok: bool, error: str = "") -> None:
        return None


def test_board_with_memory_store(tmp_path) -> None:
    store: StorePort = InMemoryStore()
    out = board(store, Settings(db_path=tmp_path / "x.db"), date(2026, 1, 5))
    assert out.green == []
    assert not (tmp_path / "x.db").exists()
