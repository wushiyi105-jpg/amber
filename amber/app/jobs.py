"""每日重算：同一自然日只排一次。"""

from __future__ import annotations

from datetime import date

from ..config import Settings
from ..ports import NotifierPort, StorePort
from .run import explain


def enqueue_daily(store: StorePort, today: date) -> bool:
    return store.enqueue(f"amber:{today}", "daily_recalc", today.isoformat(), today)


def run_due(store: StorePort, settings: Settings, today: date, notifier: NotifierPort) -> int:
    sent = 0
    for job in store.due_jobs(today):
        b, text = explain(store, settings, today)
        ok = notifier.send(f"风险看板 {today}\n红 {len(b.red)} 黄 {len(b.yellow)}\n{text}")
        store.finish_job(job.id, ok, "" if ok else "推送失败")
        sent += int(ok)
    return sent
