"""端口：app 实际调用的方法集合，实现见 adapters。"""

from __future__ import annotations

from datetime import date
from typing import Any, Protocol, runtime_checkable

from ..domain.models import Dep, Snapshot, Task


@runtime_checkable
class StorePort(Protocol):
    def list_tasks(self) -> list[Task]: ...

    def list_deps(self) -> list[Dep]: ...

    def list_snapshots(self) -> list[Snapshot]: ...

    def enqueue(self, idem_key: str, kind: str, payload: str, due_on: date) -> bool: ...
    def due_jobs(self, today: date) -> list[Any]: ...
    def finish_job(self, job_id: int, ok: bool, error: str = "") -> None: ...


@runtime_checkable
class LLMPort(Protocol):
    def write(self, system: str, facts: str) -> str: ...


@runtime_checkable
class NotifierPort(Protocol):
    def send(self, text: str) -> bool: ...
