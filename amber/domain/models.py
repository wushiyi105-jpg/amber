"""领域对象：任务、依赖、每周快照。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    points: int
    done_points: int
    due_on: date
    owner: str = ""
    started_on: date | None = None

    @property
    def remaining(self) -> int:
        return max(0, self.points - self.done_points)


@dataclass(frozen=True)
class Dep:
    id: int
    task_id: int
    blocked_by: int


@dataclass(frozen=True)
class Snapshot:
    id: int
    week_end: date
    completed_points: int


@dataclass
class Finding:
    rule_id: str
    message: str
    penalty: int
    target: str = ""


@dataclass
class Risk:
    task_id: int
    title: str
    level: str
    forecast: date | None
    reason: str


@dataclass
class Board:
    green: list[Risk] = field(default_factory=list)
    yellow: list[Risk] = field(default_factory=list)
    red: list[Risk] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    avg_points: float | None = None

    @property
    def penalty_total(self) -> int:
        return sum(f.penalty for f in self.findings)
