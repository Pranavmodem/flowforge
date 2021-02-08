"""Seal a workflow, compile its dependencies, and simulate task outcomes."""

import argparse
import hashlib
import heapq
import json
import re
from dataclasses import dataclass
from typing import Tuple

TASK_NAME = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")


@dataclass(frozen=True)
class Task:
    name: str
    needs: Tuple[str, ...]


@dataclass(frozen=True)
class Spec:
    tasks: Tuple[Task, ...]


def seal(data):
    if not isinstance(data, dict) or set(data) != {"tasks"}:
        raise ValueError("spec must contain tasks")
    entries = data["tasks"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("tasks must be a nonempty list")
    tasks = {}
    for entry in entries:
        if not isinstance(entry, dict) or not {"name"} <= entry.keys() <= {"name", "needs"}:
            raise ValueError("invalid task definition")
        name = entry["name"]
        if not _valid_name(name) or name in tasks:
            raise ValueError("invalid or duplicate task name")
        needs = entry.get("needs", [])
        if not isinstance(needs, list) or not all(_valid_name(item) for item in needs):
            raise ValueError("invalid dependency list for " + name)
        if len(needs) != len(set(needs)):
            raise ValueError("duplicate dependency for " + name)
        tasks[name] = Task(name, tuple(sorted(needs)))
    for task in tasks.values():
        missing = set(task.needs) - tasks.keys()
        if missing:
            raise ValueError("unknown dependencies for {}: {}".format(task.name, ", ".join(sorted(missing))))
    spec = Spec(tuple(tasks[name] for name in sorted(tasks)))
    compile_order(spec)
    return spec


def _valid_name(value):
    return isinstance(value, str) and TASK_NAME.fullmatch(value) is not None


def compile_order(spec):
    waiting = {task.name: len(task.needs) for task in spec.tasks}
    downstream = {task.name: [] for task in spec.tasks}
    for task in spec.tasks:
        for dependency in task.needs:
            downstream[dependency].append(task.name)

    ready = [name for name, count in waiting.items() if count == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        current = heapq.heappop(ready)
        order.append(current)
        for dependent in downstream[current]:
            waiting[dependent] -= 1
            if waiting[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(order) != len(spec.tasks):
        raise ValueError("workflow contains a dependency cycle")
    return order


def preview(spec, failures=()):
    order = compile_order(spec)
    tasks = {task.name: task.needs for task in spec.tasks}
    failures = set(failures)
    if not failures <= tasks.keys():
        raise ValueError("unknown task selected for failure")
    status = {}
    for name in order:
        if any(status[dependency] != "passed" for dependency in tasks[name]):
            status[name] = "blocked"
        else:
            status[name] = "failed" if name in failures else "passed"

    canonical = json.dumps(tasks, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"spec_sha256": hashlib.sha256(canonical).hexdigest(), "order": order, "status": status}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--fail", action="append", default=[])
    args = parser.parse_args()
    try:
        with open(args.spec, encoding="utf-8") as source:
            spec = seal(json.load(source))
        print(json.dumps(preview(spec, args.fail), indent=2, sort_keys=True))
    except (OSError, ValueError) as exc:
        parser.exit(2, "flowforge: {}\n".format(exc))


if __name__ == "__main__":
    main()
