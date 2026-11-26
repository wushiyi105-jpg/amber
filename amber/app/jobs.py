"""每日重算：同一自然日只排一次。"""

from __future__ import annotations

from datetime import date

from ..adapters.notify import WebhookNotifier
from ..adapters.store import SqliteStore
from ..config import Settings
from .run import explain


def enqueue_daily(store: SqliteStore, today: date) -> bool:
    return store.enqueue(f"amber:{today}", "daily_recalc", today.isoformat(), today)


def run_due(store: SqliteStore, settings: Settings, today: date) -> int:
    notifier = WebhookNotifier(settings.webhook_url)
    sent = 0
    for job in store.due_jobs(today):
        b, text = explain(store, settings, today)
        ok = notifier.send(f"风险看板 {today}\n红 {len(b.red)} 黄 {len(b.yellow)}\n{text}")
        store.finish_job(job.id, ok, "" if ok else "推送失败")
        sent += int(ok)
    return sent
