"""负荷：未来两周任务量 / 可用工时，超过 120% 必红。"""

from __future__ import annotations

from datetime import date, timedelta

from ..models import Finding, Task

HOURS_PER_POINT = 4.0
LIMIT = 1.2
PENALTY = 8


def ratio(tasks: list[Task], today: date, capacity_hours: float) -> float:
    horizon = today + timedelta(days=14)
    points = sum(t.remaining for t in tasks if today <= t.due_on <= horizon)
    if capacity_hours <= 0:
        raise ValueError("两周可用工时必须为正")
    return points * HOURS_PER_POINT / capacity_hours


def check(tasks: list[Task], today: date, capacity_hours: float) -> list[Finding]:
    r = ratio(tasks, today, capacity_hours)
    if r <= LIMIT:
        return []
    return [
        Finding(
            "load.over",
            f"未来两周负荷 {r:.0%}，超过 120%，排不进",
            PENALTY,
            "load",
        )
    ]
