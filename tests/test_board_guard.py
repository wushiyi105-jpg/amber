from __future__ import annotations

from datetime import date

from amber.app.run import allowed_numbers, guard
from amber.domain.engine import build
from amber.domain.models import Dep, Snapshot, Task


def _board(today=date(2026, 11, 27)):
    tasks = [
        Task(1, "支付重构", 21, 13, date(2026, 12, 4)),
        Task(2, "导出服务", 5, 1, date(2026, 11, 24)),
        Task(3, "登录改造", 3, 3, date(2026, 11, 18)),
    ]
    snaps = [Snapshot(i, date(2026, 11, 1 + 7 * i), v) for i, v in enumerate([9, 7, 8, 6])]
    return build(tasks, [], snaps, today, 40)


def test_overdue_goes_red():
    b = _board()
    titles = [r.title for r in b.red]
    assert "导出服务" in titles
    assert any(f.rule_id == "escalate.red" for f in b.findings)


def test_late_forecast_in_red():
    b = _board()
    assert "支付重构" in [r.title for r in b.red]
    assert any(f.rule_id == "forecast.late" for f in b.findings)


def test_done_task_in_green():
    b = _board()
    assert "登录改造" in [r.title for r in b.green]


def test_cycle_raises():
    tasks = [Task(1, "A", 3, 0, date(2026, 12, 1)), Task(2, "B", 3, 0, date(2026, 12, 1))]
    deps = [Dep(1, 1, 2), Dep(2, 2, 1)]
    import pytest

    with pytest.raises(ValueError):
        build(tasks, deps, [], date(2026, 11, 27), 40)


def test_guard_drops_unknown_date():
    b = _board()
    text, findings = guard("支付重构预计 2026-12-18 完成\n另一项 2027-01-01 完成", allowed_numbers(b))
    assert "2027-01-01" not in text
    assert findings[0].rule_id == "guard.number"
