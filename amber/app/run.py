"""用例：算看板、模型写风险说明、数字守卫。"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from ..config import Settings
from ..domain.engine import build
from ..domain.models import Board, Finding
from ..ports import LLMPort, StorePort

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "explain.md").read_text(encoding="utf-8")

DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
NUM = re.compile(r"\d+(?:\.\d+)?")
PENALTY = 8


def board(store: StorePort, settings: Settings, today: date | None = None) -> Board:
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


def explain(
    store: StorePort, settings: Settings, today: date | None = None, llm: LLMPort | None = None
) -> tuple[Board, str]:
    b = board(store, settings, today)
    if llm is None:
        return b, facts(b)
    try:
        raw = llm.write(PROMPT, facts(b))
    except Exception:  # noqa: BLE001
        return b, facts(b)
    text, findings = guard(raw, allowed_numbers(b))
    b.findings.extend(findings)
    return b, text or facts(b)
