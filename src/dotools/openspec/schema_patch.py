"""Line-oriented patching of the upstream ``schema.yaml``.

The upstream schema is YAML, but it is edited line-by-line rather than
round-tripped through a YAML parser so that comments, ordering and formatting
of the untouched parts are preserved exactly.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from dotools.openspec.errors import SchemaGenerationError
from dotools.openspec.overlay import Overlay, TaskArtifact

_NAME_PATTERN = re.compile(r"^name:\s*spec-driven\s*$", re.MULTILINE)
_ARTIFACT_ID = re.compile(r"^  - id:\s*(?P<id>\S+)\s*$")
_ARTIFACT_BOUNDARY = re.compile(r"^  - id:")
_APPLY_KEY = re.compile(r"^apply:\s*$")
_INSTRUCTION_KEY = re.compile(r"^  instruction:\s*[|>]\s*$")

_ARTIFACT_INDENT = "    "
_INSTRUCTION_INDENT = "    "


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _find_unique(
    lines: list[str], predicate: Callable[[str], bool], message: str
) -> int:
    """Return the index of the single matching line, or raise ``message``."""
    matches = [index for index, line in enumerate(lines) if predicate(line)]
    if len(matches) != 1:
        raise SchemaGenerationError(message)
    return matches[0]


def _block_end(
    lines: list[str], start: int, is_boundary: Callable[[str], bool]
) -> int:
    """Return the index of the first boundary line after ``start``."""
    for index in range(start + 1, len(lines)):
        if is_boundary(lines[index]):
            return index
    return len(lines)


def _rename_schema(schema_text: str, schema_name: str) -> str:
    if len(_NAME_PATTERN.findall(schema_text)) != 1:
        raise SchemaGenerationError(
            "The upstream schema name changed; review the overlay before regenerating."
        )
    return _NAME_PATTERN.sub(f"name: {schema_name}", schema_text, count=1)


def _task_artifact_block(lines: list[str], artifact: TaskArtifact) -> list[str]:
    start = _find_unique(
        lines,
        lambda line: (match := _ARTIFACT_ID.match(line)) is not None
        and match.group("id") == artifact.id,
        "The upstream tasks artifact moved or changed; review the overlay.",
    )
    end = _block_end(
        lines,
        start,
        lambda line: _ARTIFACT_BOUNDARY.match(line) is not None
        or _APPLY_KEY.match(line) is not None,
    )
    return lines[start:end]


def _verify_task_artifact(block: list[str], artifact: TaskArtifact) -> None:
    text = "\n".join(block)
    for field in ("generates", "template"):
        expected = f"{_ARTIFACT_INDENT}{field}: {getattr(artifact, field)}"
        if expected not in text:
            raise SchemaGenerationError(
                "The upstream tasks artifact paths changed; review the overlay."
            )


def _apply_block(lines: list[str]) -> tuple[int, int]:
    start = _find_unique(
        lines,
        lambda line: _APPLY_KEY.match(line) is not None,
        "The upstream apply configuration moved or changed.",
    )
    end = _block_end(lines, start, lambda line: bool(line.strip()) and _indent(line) == 0)
    return start, end


def _verify_apply_tracks(apply_lines: list[str], artifact: TaskArtifact) -> None:
    expected = f"tracks: {artifact.generates}"
    if not any(line.strip() == expected for line in apply_lines):
        raise SchemaGenerationError(
            "The upstream apply.tracks value changed; review the overlay."
        )


def _replace_apply_instruction(
    apply_lines: list[str], instruction: str
) -> list[str]:
    start = _find_unique(
        apply_lines,
        lambda line: _INSTRUCTION_KEY.match(line) is not None,
        "The upstream apply instruction format changed; review the overlay.",
    )
    end = _block_end(
        apply_lines, start, lambda line: bool(line.strip()) and _indent(line) <= 2
    )
    replacement = ["  instruction: |"]
    replacement.extend(
        f"{_INSTRUCTION_INDENT}{line}" if line else _INSTRUCTION_INDENT
        for line in instruction.splitlines()
    )
    return apply_lines[:start] + replacement + apply_lines[end:]


def patch_schema(schema_text: str, overlay: Overlay) -> str:
    """Apply the overlay to the upstream ``schema.yaml`` text."""
    artifact = overlay.expectedTaskArtifact

    schema_text = _rename_schema(schema_text, overlay.schemaName)
    lines = schema_text.splitlines()

    _verify_task_artifact(_task_artifact_block(lines, artifact), artifact)

    apply_start, apply_end = _apply_block(lines)
    apply_lines = lines[apply_start:apply_end]
    _verify_apply_tracks(apply_lines, artifact)

    lines[apply_start:apply_end] = _replace_apply_instruction(
        apply_lines, overlay.applyInstruction
    )
    return "\n".join(lines) + "\n"
