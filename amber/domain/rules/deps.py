"""依赖成环：成环直接报错，不出报告。"""

from __future__ import annotations

from ..models import Dep


def cycle(deps: list[Dep]) -> list[int] | None:
    graph: dict[int, list[int]] = {}
    for d in deps:
        graph.setdefault(d.task_id, []).append(d.blocked_by)
    visiting: set[int] = set()
    done: set[int] = set()

    def walk(node: int, path: list[int]) -> list[int] | None:
        if node in visiting:
            return path[path.index(node):] + [node]
        if node in done:
            return None
        visiting.add(node)
        for nxt in graph.get(node, []):
            found = walk(nxt, path + [node])
            if found:
                return found
        visiting.remove(node)
        done.add(node)
        return None

    for node in list(graph):
        found = walk(node, [])
        if found:
            return found
    return None
