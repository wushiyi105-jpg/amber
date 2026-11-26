"""命令行：seed / board / explain / jobs / doctor / serve。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ..adapters.store import SqliteStore
from ..app.jobs import enqueue_daily, run_due
from ..app.run import board, explain
from ..config import Settings
from ..config import settings as default_settings
from ..doctor import main as doctor_main

app = typer.Typer(help="项目风险：哪件事会延期", no_args_is_help=True)
console = Console()


def _settings(db: Path | None, port: int | None = None) -> Settings:
    s = default_settings.model_copy(deep=True)
    if db:
        s.db_path = db
    if port:
        s.port = port
    return s


def _store(settings: Settings) -> SqliteStore:
    return SqliteStore(settings.db_path)


@app.command()
def seed(db: Path = typer.Option(None)) -> None:
    """写入任务、依赖与 4 周快照。"""
    s = _settings(db)
    store = _store(s)
    data = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "seed.json").read_text(encoding="utf-8")
    )
    ids: dict[str, int] = {}
    for t in data["tasks"]:
        ids[t["title"]] = store.add_task(
            t["title"], t["points"], t.get("done_points", 0), date.fromisoformat(t["due"]), t.get("owner", "")
        )
    for d in data["deps"]:
        store.add_dep(ids[d["task"]], ids[d["blocked_by"]])
    for srow in data["snapshots"]:
        store.add_snapshot(date.fromisoformat(srow["week_end"]), srow["completed"])
    console.print(f"已写入 {len(data['tasks'])} 个任务、{len(data['deps'])} 条依赖、{len(data['snapshots'])} 周快照")


@app.command("board")
def board_cmd(day: str = typer.Option(""), db: Path = typer.Option(None)) -> None:
    """看板三列与扣分。"""
    s = _settings(db)
    d = date.fromisoformat(day) if day else date.today()
    try:
        b = board(_store(s), s, d)
    except ValueError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc
    table = Table(title=f"风险看板 {d}")
    table.add_column("列")
    table.add_column("任务")
    table.add_column("预测")
    for color, rows in [("红", b.red), ("黄", b.yellow), ("绿", b.green)]:
        for r in rows:
            table.add_row(color, r.title, r.forecast.isoformat() if r.forecast else "—")
    console.print(table)
    for f in b.findings:
        console.print(f"  [yellow]{f.rule_id}[/] -{f.penalty} {f.message}")




@app.command("explain")
def explain_cmd(day: str = typer.Option(""), db: Path = typer.Option(None)) -> None:
    """模型说明（无 key 走本地事实）。"""
    s = _settings(db)
    d = date.fromisoformat(day) if day else date.today()
    b, text = explain(_store(s), s, d)
    console.print(text)
    console.print(f"红 {len(b.red)} 黄 {len(b.yellow)} 绿 {len(b.green)}，扣分 {b.penalty_total}")




@app.command()
def jobs(
    day: str = typer.Option(""), run: bool = typer.Option(False, "--run"), db: Path = typer.Option(None)
) -> None:
    """每日重算任务。"""
    s = _settings(db)
    d = date.fromisoformat(day) if day else date.today()
    store = _store(s)
    if run:
        console.print(f"发出 {run_due(store, s, d)} 条")
        return
    console.print("已入队" if enqueue_daily(store, d) else "今天已排过")


@app.command()
def doctor(db: Path = typer.Option(None)) -> None:
    """四项体检。"""
    raise typer.Exit(code=doctor_main(_settings(db)))


@app.command()
def serve(port: int = typer.Option(None), db: Path = typer.Option(None)) -> None:
    """Web 界面。"""
    import uvicorn

    from .web import create_app

    s = _settings(db, port)
    uvicorn.run(create_app(s), host="127.0.0.1", port=s.port)


if __name__ == "__main__":
    app()
