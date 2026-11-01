"""Atomic installation of a generated schema plus its state file."""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from dotools.openspec.overlay import Overlay


@dataclass(frozen=True)
class InstallState:
    """Persisted record of what was installed and from which inputs."""

    schema_name: str
    upstream_schema: str
    fingerprint: str

    @classmethod
    def state_path(cls, destination: Path, schema_name: str) -> Path:
        return destination.parent / f".{schema_name}.state.json"

    @classmethod
    def read(cls, path: Path) -> InstallState | None:
        """Return the stored state, or ``None`` when absent or unreadable."""
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(raw, dict):
            return None
        try:
            return cls(
                schema_name=raw["schemaName"],
                upstream_schema=raw["upstreamSchema"],
                fingerprint=raw["fingerprint"],
            )
        except KeyError:
            return None

    def write(self, path: Path) -> None:
        payload = {
            "schemaName": self.schema_name,
            "upstreamSchema": self.upstream_schema,
            "fingerprint": self.fingerprint,
        }
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)


def _swap_into_place(staging: Path, destination: Path, backup: Path) -> bool:
    """Move ``staging`` to ``destination``, restoring ``backup`` on failure.

    Returns ``True`` when a previous destination was moved aside and should be
    cleaned up by the caller.
    """
    moved_backup = False
    if destination.exists():
        destination.rename(backup)
        moved_backup = True
    try:
        staging.rename(destination)
    except Exception:
        if moved_backup:
            backup.rename(destination)
            moved_backup = False
        raise
    return moved_backup


def install_schema(
    *,
    staging: Path,
    destination: Path,
    overlay: Overlay,
    fingerprint: str,
) -> None:
    """Install ``staging`` at ``destination`` and record the install state."""
    schema_name = overlay.schemaName
    token = uuid.uuid4().hex[:12]
    final_staging = destination.parent / f".{schema_name}-staging-{token}"
    backup = destination.parent / f".{schema_name}-backup-{token}"
    state_path = InstallState.state_path(destination, schema_name)

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staging, final_staging)
        moved_backup = _swap_into_place(final_staging, destination, backup)
        InstallState(
            schema_name=schema_name,
            upstream_schema=overlay.upstreamSchema,
            fingerprint=fingerprint,
        ).write(state_path)
        if moved_backup:
            shutil.rmtree(backup)
    finally:
        for temporary in (final_staging, backup):
            if temporary.exists():
                shutil.rmtree(temporary, ignore_errors=True)
