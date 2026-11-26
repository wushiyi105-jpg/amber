from __future__ import annotations

from datetime import date

from amber.domain.models import Snapshot, Task
from amber.domain.rules.forecast import forecast_date, late
from amber.domain.rules.throughput import average, no_sample


def _snaps(*values):
    return [Snapshot(i, date(2026, 11, 1 + 7 * i), v) for i, v in enumerate(values)]


def test_average_uses_last_four():
    assert average(_snaps(9, 7, 8, 6, 3)) == 6.0


def test_less_than_three_samples_returns_none():
    assert average(_snaps(5, 6)) is None
    assert no_sample(_snaps(5, 6))[0].rule_id == "throughput.no_sample"


def test_enough_samples_no_finding():
    assert no_sample(_snaps(5, 6, 7)) == []


def test_forecast_rounds_up_to_whole_weeks():
    assert forecast_date(21, 7.0, date(2026, 11, 27)) == date(2026, 12, 18)


def test_late_forecast_flagged():
    task = Task(1, "支付重构", 21, 13, date(2026, 12, 4))
    findings = late(task, date(2026, 12, 18))
    assert findings[0].rule_id == "forecast.late"
    assert "14 天" in findings[0].message


def test_on_time_forecast_silent():
    task = Task(1, "支付重构", 21, 13, date(2026, 12, 25))
    assert late(task, date(2026, 12, 18)) == []

