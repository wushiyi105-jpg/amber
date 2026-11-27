"""周一风险周报：5 个项目、3 条风险、建议动作。"""

from __future__ import annotations

from datetime import date

from amber.app.weekly import build_weekly
from amber.domain.catalog import projects


def test_weekly_three_risks() -> None:
    text = build_weekly(date(2026, 11, 30))
    assert "## 一、本周 3 条风险" in text
    assert text.count("### ") >= 3
    assert text.count("建议动作") >= 3
    assert "5 个项目一眼看" in text
    assert "风险分级口径" in text


def test_projects_are_five() -> None:
    assert len(projects()) == 5
    assert sum(len(p["tasks"]) for p in projects()) == 25
