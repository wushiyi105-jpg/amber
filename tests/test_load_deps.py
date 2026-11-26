from __future__ import annotations

from datetime import date

from amber.domain.models import Dep, Task
from amber.domain.rules.deps import cycle
from amber.domain.rules.load import check, ratio


def _tasks():
    return [
        Task(1, "A", 10, 0, date(2026, 12, 1)),
        Task(2, "B", 5, 0, date(2026, 12, 3)),
    ]


def test_load_over_120_percent_flagged():
    findings = check(_tasks(), date(2026, 11, 27), 40)
    assert findings[0].rule_id == "load.over"


def test_load_within_capacity_silent():
    assert check(_tasks(), date(2026, 11, 27), 100) == []


def test_ratio_ignores_far_tasks():
    far = [Task(3, "C", 20, 0, date(2027, 3, 1))]
    assert ratio(far, date(2026, 11, 27), 40) == 0


def test_cycle_detected():
    deps = [Dep(1, 1, 2), Dep(2, 2, 3), Dep(3, 3, 1)]
    assert cycle(deps) == [1, 3, 2, 1] or cycle(deps) is not None


def test_acyclic_graph_ok():
    assert cycle([Dep(1, 1, 2), Dep(2, 2, 3)]) is None
