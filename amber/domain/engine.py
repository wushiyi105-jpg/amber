"""看板：按预测与负荷分绿黄红。"""

from __future__ import annotations

from datetime import date

from .models import Board, Dep, Finding, Risk, Snapshot, Task
from .rules.deps import cycle
from .rules.forecast import forecast_date, late
from .rules.load import check as load_check
from .rules.throughput import average, no_sample

OVERDUE_RED_DAYS = 3


def build(
    tasks: list[Task],
    deps: list[Dep],
    snapshots: list[Snapshot],
    today: date,
    capacity_hours: float,
) -> Board:
    ring = cycle(deps)
    if ring:
        raise ValueError(f"依赖成环：{' -> '.join(str(x) for x in ring)}")
    board = Board()
    board.findings += no_sample(snapshots)
    avg = average(snapshots)
    board.avg_points = avg
    board.findings += load_check(tasks, today, capacity_hours)
    for t in tasks:
        overdue = (today - t.due_on).days
        if t.remaining == 0:
            board.green.append(Risk(t.id, t.title, "green", None, "已完成"))
            continue
        if overdue >= OVERDUE_RED_DAYS:
            board.red.append(Risk(t.id, t.title, "red", None, f"已逾期 {overdue} 天"))
            board.findings.append(
                Finding("escalate.red", f"{t.title} 逾期 {overdue} 天，进红列", 4, t.title)
            )
            continue
        if avg is None:
            board.yellow.append(Risk(t.id, t.title, "yellow", None, "样本不足，不预测"))
            continue
        f = forecast_date(t.remaining, avg, today)
        late_findings = late(t, f)
        if late_findings:
            board.findings += late_findings
            board.red.append(Risk(t.id, t.title, "red", f, late_findings[0].message))
        else:
            board.yellow.append(Risk(t.id, t.title, "yellow", f, f"预测 {f} 可完成"))
    return board
