"""吞吐：至少 3 周完整快照才预测，否则只报负荷。"""

from __future__ import annotations

from ..models import Finding, Snapshot

MIN_SAMPLES = 3


def average(snapshots: list[Snapshot], keep: int = 4) -> float | None:
    rows = sorted(snapshots, key=lambda s: s.week_end)[-keep:]
    if len(rows) < MIN_SAMPLES:
        return None
    return sum(r.completed_points for r in rows) / len(rows)


def no_sample(snapshots: list[Snapshot]) -> list[Finding]:
    if len(snapshots) >= MIN_SAMPLES:
        return []
    return [
        Finding(
            "throughput.no_sample",
            f"只有 {len(snapshots)} 周快照，少于 {MIN_SAMPLES} 周，只报负荷不报完工日",
            0,
            "snapshots",
        )
    ]
