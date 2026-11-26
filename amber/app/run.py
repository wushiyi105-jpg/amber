"""用例：算看板、模型写风险说明、数字守卫。"""

from __future__ import annotations

import re
from datetime import date

from ..adapters.llm import build_llm
from ..adapters.store import SqliteStore
from ..config import Settings
from ..domain.engine import build
from ..domain.models import Board, Finding

PROMPT = """你在解释项目风险。只能引用输入里出现的日期与点数。
输出两段：为什么黄/红（不超过 3 句）；砍什么或加谁（2 条以内）。
不要预测输入里没有的日期，不要编人名。"""

DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
NUM = re.compile(r"\d+(?:\.\d+)?")
PENALTY = 8


def board(store: SqliteStore, settings: Settings, today: date | None = None) -> Board:
    return build(
        store.list_tasks(), store.list_deps(), store.list_snapshots(),
        today or date.today(), settings.capacity_hours,
    )


def facts(board: Board) -> str:
    lines = [f"周吞吐均值={board.avg_points}", f"红={len(board.red)} 黄={len(board.yellow)} 绿={len(board.green)}"]
    for r in board.red + board.yellow:
        lines.append(f"- {r.title} 预测={r.forecast or '无'} 原因={r.reason}")
    for f in board.findings:
        lines.append(f"扣分 {f.rule_id} {f.message}")
    return "\n".join(lines)


def allowed_numbers(board: Board) -> set[str]:
    out: set[str] = set()
    for r in board.red + board.yellow:
        out.update(NUM.findall(r.reason))
        if r.forecast:
            out.add(r.forecast.isoformat())
    if board.avg_points is not None:
        out.add(f"{board.avg_points:.1f}")
        out.add(str(int(board.avg_points)))
    out.update({"3", "120"})
    return out


def guard(text: str, allowed: set[str]) -> tuple[str, list[Finding]]:
    kept: list[str] = []
    findings: list[Finding] = []
    for line in text.splitlines():
        bad = [n for n in NUM.findall(line) if n not in allowed]
        bad += [d for d in DATE.findall(line) if d not in allowed]
        if bad:
            findings.append(Finding("guard.number", f"丢弃一行：含输入外数字 {sorted(set(bad))}", PENALTY, line[:40]))
            continue
        kept.append(line)
    return "\n".join(kept).strip(), findings


def explain(store: SqliteStore, settings: Settings, today: date | None = None) -> tuple[Board, str]:
    b = board(store, settings, today)
    if not settings.llm_enabled:
        return b, facts(b)
    llm = build_llm(settings.llm_base_url, settings.llm_api_key, settings.llm_model, PROMPT)
    try:
        raw = llm.write(PROMPT, facts(b))
    except Exception:  # noqa: BLE001
        return b, facts(b)
    text, findings = guard(raw, allowed_numbers(b))
    b.findings.extend(findings)
    return b, text or facts(b)
