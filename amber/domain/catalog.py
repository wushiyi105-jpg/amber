"""5 个项目样本、风险分级、依赖类型。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parents[2] / "data"


@lru_cache(maxsize=1)
def _data() -> dict[str, Any]:
    return json.loads((DATA / "projects.json").read_text(encoding="utf-8"))


def projects() -> list[dict[str, Any]]:
    return list(_data()["projects"])


def grading() -> dict[str, str]:
    return dict(_data()["grading"])


def dep_types() -> list[dict[str, str]]:
    return list(_data()["dep_types"])
