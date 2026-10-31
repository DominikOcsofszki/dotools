"""Thin wrapper around the external ``openspec`` CLI."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from dotools.openspec.errors import SchemaGenerationError

_PATH_PATTERN = re.compile(r"^Path:\s*(.+)$", re.MULTILINE)


def run_openspec(args: list[str], cwd: Path) -> str:
    """Run ``openspec`` with ``args`` and return stdout, raising on failure."""
    try:
        result = subprocess.run(
            ["openspec", *args],
            cwd=cwd,
            check=False,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as error:
        raise SchemaGenerationError(
            "The openspec CLI is not installed or not on PATH."
        ) from error

    if result.returncode:
        raise SchemaGenerationError(
            f"openspec {' '.join(args)} failed ({result.returncode}):\n"
            f"{result.stderr or result.stdout}"
        )
    return result.stdout


def resolve_installed_schema(upstream_schema: str, cwd: Path) -> Path:
    """Locate the installed upstream schema directory via ``openspec schema which``."""
    output = run_openspec(["schema", "which", upstream_schema], cwd)
    match = _PATH_PATTERN.search(output)
    if not match:
        raise SchemaGenerationError(
            f"Could not resolve the installed {upstream_schema} schema path."
        )

    try:
        source_dir = Path(match.group(1).strip()).resolve(strict=True)
    except OSError as error:
        raise SchemaGenerationError(
            f"Resolved schema path does not exist: {match.group(1).strip()}"
        ) from error

    if not (source_dir / "schema.yaml").is_file():
        raise SchemaGenerationError(f"Resolved schema has no schema.yaml: {source_dir}")
    return source_dir


def validate_schema(schema_name: str, cwd: Path) -> str:
    """Validate a staged schema, returning any informational output."""
    return run_openspec(["schema", "validate", schema_name], cwd).strip()
