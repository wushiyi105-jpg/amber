"""完工预测：剩余点数 / 周吞吐 → 周数 → 日期。"""

from __future__ import annotations

import math
from datetime import date, timedelta

from ..models import Finding, Task

PENALTY = 6


def forecast_date(remaining: int, avg: float, today: date) -> date:
    if avg <= 0:
        raise ValueError("吞吐均值必须为正")
    weeks = math.ceil(remaining / avg)
    return today + timedelta(days=7 * max(1, weeks))


def late(task: Task, forecast: date) -> list[Finding]:
    if forecast <= task.due_on:
        return []
    days = (forecast - task.due_on).days
    return [
        Finding(
            "forecast.late",
            f"{task.title} 按当前吞吐要晚 {days} 天（预测 {forecast}，承诺 {task.due_on}）",
            PENALTY,
            task.title,
        )
    ]
