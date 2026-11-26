from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from amber.doctor import run_doctor
from amber.iface.cli import app
from amber.iface.web import create_app


def _seed(store):
    store.add_task("支付重构", 21, 13, date(2026, 12, 4))
    store.add_snapshot(date(2026, 11, 1), 9)
    store.add_snapshot(date(2026, 11, 8), 7)
    store.add_snapshot(date(2026, 11, 15), 8)


def test_web_board(store, settings):
    _seed(store)
    client = TestClient(create_app(settings, store))
    resp = client.get("/")
    assert resp.status_code == 200
    assert "支付重构" in resp.text


def test_web_cycle_shows_error(store, settings):
    a = store.add_task("A", 3, 0, date(2026, 12, 1))
    b = store.add_task("B", 3, 0, date(2026, 12, 1))
    store.add_dep(a, b)
    store.add_dep(b, a)
    client = TestClient(create_app(settings, store))
    assert "依赖成环" in client.get("/").text


def test_cli_board_and_bad_day(tmp_path):
    runner = CliRunner()
    db = str(tmp_path / "c.db")
    assert runner.invoke(app, ["board", "--db", db, "--day", "2026-11-27"]).exit_code == 0
    assert runner.invoke(app, ["board", "--db", db, "--day", "2026-13-01"]).exit_code != 0


def test_doctor_green(settings):
    checks, ok = run_doctor(settings)
    assert ok is True
