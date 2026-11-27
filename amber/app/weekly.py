"""周一风险周报：5 个项目 → 3 条风险 + 建议动作。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from ..domain.catalog import dep_types, grading, projects
from ..domain.engine import build
from ..domain.models import Dep, Snapshot, Task
from ..domain.rules.load import ratio
from ..domain.rules.throughput import average


@dataclass
class Picked:
    project: str
    title: str
    level: str
    reason: str
    score: int
    action: str


def _action(level: str, reason: str) -> str:
    if "逾期" in reason:
        return "今天砍掉非关键验收项，把剩余点拆到人天；周五只保一个可上线范围。"
    if "要晚" in reason:
        return "按预测日期倒排：本周先交能验收的最小范围；要按期就加 1 人，不加就改承诺日。"
    if "上游" in reason:
        return "先锁上游交付日，再决定下游是否顺延；联调前不要再加新需求。"
    if "负荷" in reason:
        return "从低优先级项目抽 1 人，或砍 20% 范围；本周不再接新需求。"
    if "样本" in reason:
        return "补两周快照，或改用剩余点/人天估算；先只报负荷，不承诺日期。"
    return "按周复盘剩余点，盯住关键路径，不扩范围。"


def build_weekly(today: date) -> str:
    all_risks: list[Picked] = []
    summary_rows: list[str] = []

    for project in projects():
        tasks: list[Task] = []
        ids: dict[str, int] = {}
        for idx, t in enumerate(project["tasks"], 1):
            ids[t["title"]] = idx
            tasks.append(
                Task(idx, t["title"], t["points"], t["done_points"], date.fromisoformat(t["due"]), t["owner"])
            )
        deps = [
            Dep(i, ids[d["task"]], ids[d["blocked_by"]])
            for i, d in enumerate(project["deps"], 1)
        ]
        snaps = [
            Snapshot(i, today - timedelta(weeks=len(project["snapshots"]) - i), c)
            for i, c in enumerate(project["snapshots"], 1)
        ]
        b = build(tasks, deps, snaps, today, project["capacity_hours"])
        avg = average(snaps)
        load = ratio(tasks, today, project["capacity_hours"])
        summary_rows.append(
            f"| {project['name']} | {len(tasks)} | {len(b.red)} | {len(b.yellow)} | {len(b.green)} | "
            f"{load:.0%} | {avg:.1f} 点/周 |" if avg else
            f"| {project['name']} | {len(tasks)} | {len(b.red)} | {len(b.yellow)} | {len(b.green)} | "
            f"{load:.0%} | 样本不足 |"
        )

        by_id = {t.id: t for t in tasks}
        risk_titles = {r.title: r for r in [*b.red, *b.yellow]}
        for r in [*b.red, *b.yellow]:
            score = 100 if r.level == "red" else 40
            if r.forecast and r.forecast > by_id[r.task_id].due_on:
                score += (r.forecast - by_id[r.task_id].due_on).days
            all_risks.append(
                Picked(project["name"], r.title, r.level, r.reason, score, _action(r.level, r.reason))
            )

        for d in project["deps"]:
            up = by_id[ids[d["blocked_by"]]]
            down = by_id[ids[d["task"]]]
            up_risk = risk_titles.get(up.title)
            if up_risk and down.title not in risk_titles:
                all_risks.append(
                    Picked(
                        project["name"],
                        down.title,
                        "yellow",
                        f"上游《{up.title}》{up_risk.reason}，{d.get('type', '硬依赖')}会传导",
                        65,
                        _action("yellow", "上游"),
                    )
                )

        if load > 1.2:
            all_risks.append(
                Picked(
                    project["name"],
                    "项目整体负荷",
                    "red",
                    f"未来两周负荷 {load:.0%}，超过 120%",
                    90,
                    _action("red", "负荷"),
                )
            )

    all_risks.sort(key=lambda r: r.score, reverse=True)
    picked = all_risks[:3]

    lines = [
        f"# 项目风险周报 · {today.isoformat()}",
        "",
        "> 周一发群版：只讲 3 条最可能延期的风险，每条给一个动作。状态由剩余点、吞吐和依赖算出来，不看人手填的状态栏。",
        "",
        "## 一、本周 3 条风险",
        "",
    ]
    if not picked:
        lines.append("本周没有需要升级的风险。")
    for i, p in enumerate(picked, 1):
        lines += [
            f"### {i}. [{p.level.upper()}] {p.project} / {p.title}",
            "",
            f"- 为什么：{p.reason}",
            f"- 建议动作：{p.action}",
            "",
        ]

    lines += [
        "## 二、5 个项目一眼看",
        "",
        "| 项目 | 任务 | 红 | 黄 | 绿 | 两周负荷 | 吞吐 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *summary_rows,
        "",
        "## 三、风险分级口径",
        "",
    ]
    for k, v in grading().items():
        lines.append(f"- **{k}**：{v}")
    lines += ["", "## 四、依赖类型", ""]
    for d in dep_types():
        lines.append(f"- **{d['type']}**：{d['rule']}")

    lines += [
        "",
        "---",
        "",
        f"数据来源：`data/projects.json` 的 5 个项目、25 个任务、4 周吞吐快照；"
        f"本报告由本地规则计算，未调用模型。共评估 {len(all_risks)} 条风险，取分数最高的 3 条。",
        "",
    ]
    return "\n".join(lines)
