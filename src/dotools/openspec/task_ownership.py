"""Validation of workstream ownership paths in OpenSpec task files."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from dotools.openspec.errors import SchemaGenerationError

_BATCH_HEADING = re.compile(r"^##\s+(\d+)\.")
_TASK_CHECKBOX = re.compile(r"^\s*-\s+\[[ xX]\]\s+(\d+\.\d+)\b")
_PATHS_LINE = re.compile(r"^\s+-\s+paths:\s*(.*?)\s*$")


def _read_tasks(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise SchemaGenerationError(
            f"Could not read tasks file {path}: {error}"
        ) from error


def _parse_paths(value: str, task_id: str) -> list[PurePosixPath]:
    if value == "none":
        return []
    raw_paths = re.findall(r"`([^`]+)`", value)
    remainder = re.sub(r"`[^`]+`", "", value).strip().strip(",")
    if not raw_paths or remainder:
        raise SchemaGenerationError(
            f"Task {task_id} must declare paths as backtick-delimited "
            "repository-relative paths or `none`."
        )

    paths: list[PurePosixPath] = []
    for raw_path in raw_paths:
        normalized = raw_path.replace("\\", "/")
        path = PurePosixPath(normalized)
        if (
            not normalized
            or path.is_absolute()
            or not path.parts
            or ".." in path.parts
            or re.match(r"^[A-Za-z]:", normalized)
        ):
            raise SchemaGenerationError(
                f"Task {task_id} has an invalid ownership path: {raw_path!r}."
            )
        paths.append(path)
    return paths


def _paths_overlap(first: PurePosixPath, second: PurePosixPath) -> bool:
    shortest = min(len(first.parts), len(second.parts))
    return first.parts[:shortest] == second.parts[:shortest]


def validate_task_ownership(path: Path) -> list[str]:
    """Return a list of ownership problems found in ``tasks.md``."""
    lines = _read_tasks(path)
    batches: dict[str, list[tuple[str, list[PurePosixPath]]]] = {}
    current_batch: str | None = None
    current_task: tuple[str, int] | None = None
    task_blocks: list[tuple[str, str, int, int]] = []

    for index, line in enumerate(lines):
        heading = _BATCH_HEADING.match(line)
        if heading:
            if current_task is not None:
                task_blocks.append(
                    (current_batch or "?", current_task[0], current_task[1], index)
                )
                current_task = None
            current_batch = heading.group(1)
            continue

        task = _TASK_CHECKBOX.match(line)
        if task:
            if current_batch is None:
                raise SchemaGenerationError(
                    f"Task {task.group(1)} appears before a numbered batch heading."
                )
            if current_task is not None:
                task_blocks.append(
                    (current_batch, current_task[0], current_task[1], index)
                )
            if task.group(1).split(".", maxsplit=1)[0] != current_batch:
                raise SchemaGenerationError(
                    f"Task {task.group(1)} does not belong to batch {current_batch}."
                )
            current_task = (task.group(1), index)

    if current_task is not None:
        task_blocks.append(
            (current_batch or "?", current_task[0], current_task[1], len(lines))
        )

    if not task_blocks:
        raise SchemaGenerationError(f"No numbered tracked tasks found in {path}.")

    for batch_id, task_id, start, end in task_blocks:
        declarations = [
            match.group(1)
            for line in lines[start + 1 : end]
            if (match := _PATHS_LINE.match(line)) is not None
        ]
        if len(declarations) != 1:
            raise SchemaGenerationError(
                f"Task {task_id} must have exactly one indented `paths:` line."
            )
        batches.setdefault(batch_id, []).append(
            (task_id, _parse_paths(declarations[0], task_id))
        )

    problems: list[str] = []
    for batch_id, tasks in batches.items():
        for index, (task_id, task_paths) in enumerate(tasks):
            for other_task_id, other_paths in tasks[index + 1 :]:
                overlaps = sorted(
                    {
                        (first, second)
                        for first in task_paths
                        for second in other_paths
                        if _paths_overlap(first, second)
                    },
                    key=lambda pair: (str(pair[0]), str(pair[1])),
                )
                for first, second in overlaps:
                    problems.append(
                        f"Batch {batch_id}: task {task_id} path `{first}` "
                        f"overlaps task {other_task_id} path `{second}`."
                    )
    return problems
