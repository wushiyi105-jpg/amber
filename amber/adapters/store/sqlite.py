"""SQLite：tasks / deps / snapshots / jobs。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Date, Integer, String, Text, inspect, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from ...domain.models import Dep, Snapshot, Task
from .base import Base, make_engine, make_session


class TaskRow(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    points: Mapped[int] = mapped_column(Integer)
    done_points: Mapped[int] = mapped_column(Integer, default=0)
    due_on: Mapped[date] = mapped_column(Date)
    owner: Mapped[str] = mapped_column(String(40), default="")
    started_on: Mapped[date | None] = mapped_column(Date, nullable=True)


class DepRow(Base):
    __tablename__ = "deps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, index=True)
    blocked_by: Mapped[int] = mapped_column(Integer)


class SnapshotRow(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_end: Mapped[date] = mapped_column(Date, unique=True)
    completed_points: Mapped[int] = mapped_column(Integer)


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idem_key: Mapped[str] = mapped_column(String(80), unique=True)
    kind: Mapped[str] = mapped_column(String(24))
    payload: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(12), default="pending")
    due_on: Mapped[date] = mapped_column(Date)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")


def _upgrade_schema(engine) -> None:
    root = next(p for p in Path(__file__).resolve().parents if (p / "alembic.ini").exists())
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{engine.url.database}")
    command.upgrade(cfg, "head")


class SqliteStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.engine = make_engine(self.path)
        self.session: sessionmaker[Session] = make_session(self.engine)
        self.init_schema()

    def init_schema(self) -> None:
        _upgrade_schema(self.engine)

    def schema_ok(self) -> bool:
        return {"tasks", "deps", "snapshots", "jobs"} <= set(
            inspect(self.engine).get_table_names()
        )

    def summary(self) -> str:
        return f"{len(self.list_tasks())} 个任务、{len(self.list_snapshots())} 周快照"

    def add_task(self, title: str, points: int, done_points: int, due_on: date, owner: str = "") -> int:
        if points <= 0:
            raise ValueError("points 必须为正")
        if done_points > points:
            raise ValueError("已完成点数不能超过总量")
        with self.session() as s:
            row = TaskRow(title=title, points=points, done_points=done_points, due_on=due_on, owner=owner)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_tasks(self) -> list[Task]:
        with self.session() as s:
            rows = s.scalars(select(TaskRow)).all()
        return [Task(r.id, r.title, r.points, r.done_points, r.due_on, r.owner, r.started_on) for r in rows]

    def add_dep(self, task_id: int, blocked_by: int) -> int:
        if task_id == blocked_by:
            raise ValueError("任务不能依赖自己")
        with self.session() as s:
            row = DepRow(task_id=task_id, blocked_by=blocked_by)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_deps(self) -> list[Dep]:
        with self.session() as s:
            rows = s.scalars(select(DepRow)).all()
        return [Dep(r.id, r.task_id, r.blocked_by) for r in rows]

    def add_snapshot(self, week_end: date, completed_points: int) -> int:
        with self.session() as s:
            row = SnapshotRow(week_end=week_end, completed_points=completed_points)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_snapshots(self) -> list[Snapshot]:
        with self.session() as s:
            rows = s.scalars(select(SnapshotRow).order_by(SnapshotRow.week_end)).all()
        return [Snapshot(r.id, r.week_end, r.completed_points) for r in rows]

    def enqueue(self, idem_key: str, kind: str, payload: str, due_on: date) -> bool:
        with self.session() as s:
            if s.scalar(select(JobRow).where(JobRow.idem_key == idem_key)):
                return False
            s.add(JobRow(idem_key=idem_key, kind=kind, payload=payload, due_on=due_on))
            s.commit()
            return True

    def due_jobs(self, today: date) -> list[JobRow]:
        with self.session() as s:
            return list(s.scalars(select(JobRow).where(JobRow.status == "pending", JobRow.due_on <= today)).all())

    def finish_job(self, job_id: int, ok: bool, error: str = "") -> None:
        with self.session() as s:
            row = s.get(JobRow, job_id)
            if row is None:
                return
            row.status = "done" if ok else "pending"
            row.attempts += 1
            row.error = error
            s.commit()

