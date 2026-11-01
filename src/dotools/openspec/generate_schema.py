"""Generate a customized OpenSpec schema from the installed upstream schema.

Pipeline: resolve upstream -> fingerprint -> build staging -> validate ->
show diff -> confirm destination -> install atomically.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from dotools.openspec.cli import resolve_installed_schema, validate_schema
from dotools.openspec.errors import SchemaGenerationError
from dotools.openspec.fingerprint import compute_fingerprint
from dotools.openspec.install import InstallState, install_schema
from dotools.openspec.overlay import DEFAULT_OVERLAY_PATH, Overlay, load_overlay
from dotools.openspec.presentation import confirm_destination, print_diff
from dotools.openspec.staging import SCHEMA_FILE, build_staging
from dotools.openspec.tree import diff_trees
from dotools.sdk import AppConfig

__all__ = [
    "DEFAULT_OVERLAY_PATH",
    "SchemaGenerationError",
    "generate_schema",
]


@dataclass(frozen=True)
class GenerationRequest:
    """Resolved inputs for a single generation run."""

    overlay: Overlay
    destination: Path
    force: bool
    yes: bool

    @property
    def schema_name(self) -> str:
        return self.overlay.schemaName

    @property
    def state_path(self) -> Path:
        return InstallState.state_path(self.destination, self.schema_name)


def _resolve_request(
    *,
    cwd: Path,
    dest: Path | None,
    overlay_path: Path | None,
    force: bool,
    yes: bool,
) -> GenerationRequest:
    overlay = load_overlay(overlay_path or DEFAULT_OVERLAY_PATH)
    destination = (dest or cwd / "openspec" / "schemas" / overlay.schemaName).resolve()
    return GenerationRequest(
        overlay=overlay,
        destination=destination,
        force=force,
        yes=yes,
    )


def _is_current(request: GenerationRequest, fingerprint: str) -> bool:
    """Return ``True`` when the installed schema matches the current inputs."""
    if request.force:
        return False
    if not (request.destination / SCHEMA_FILE).is_file():
        return False
    state = InstallState.read(request.state_path)
    return state is not None and state.fingerprint == fingerprint


def _stage_and_validate(
    source_dir: Path, overlay: Overlay, work_root: Path
) -> tuple[Path, str]:
    """Build the patched staging tree and validate a copy of it."""
    staging = build_staging(source_dir, work_root / "staging", overlay)

    validation_schema = (
        work_root / "validation" / "openspec" / "schemas" / overlay.schemaName
    )
    validation_schema.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(staging, validation_schema)
    return staging, validate_schema(overlay.schemaName, work_root / "validation")


def _choose_destination(helper, request: GenerationRequest) -> Path | None:
    if request.yes:
        return request.destination
    return confirm_destination(helper, request.destination)


def generate_schema(
    *,
    deps: AppConfig,
    dest: Path | None = None,
    overlay_path: Path | None = None,
    force: bool = False,
    yes: bool = False,
    check: bool = False,
) -> None:
    """Generate and install the customized schema."""
    helper = deps.helper
    cwd = Path.cwd()
    request = _resolve_request(
        cwd=cwd,
        dest=dest,
        overlay_path=overlay_path,
        force=force,
        yes=yes,
    )
    overlay = request.overlay

    source_dir = resolve_installed_schema(overlay.upstreamSchema, cwd)
    fingerprint = compute_fingerprint(source_dir, overlay)

    if not check and _is_current(request, fingerprint):
        helper.info(f"{overlay.schemaName} is current ({fingerprint[:12]}).")
        return

    work_root = Path(tempfile.mkdtemp(prefix="dotools-schema-"))
    try:
        staging, validation_output = _stage_and_validate(source_dir, overlay, work_root)
        if validation_output:
            helper.info(validation_output)

        if check:
            diff = diff_trees(request.destination, staging)
            if diff:
                print_diff(helper, diff)
                raise SchemaGenerationError(
                    f"{overlay.schemaName} is out of date at {request.destination}; "
                    "run `dotools openspec generate-schema` to update it."
                )
            helper.success(f"{overlay.schemaName} is up to date.")
            return

        helper.rule(f"Diff: upstream {overlay.upstreamSchema} -> {overlay.schemaName}")
        diff = diff_trees(source_dir, staging)
        if diff:
            print_diff(helper, diff)
        else:
            helper.info("No differences.")

        target = _choose_destination(helper, request)
        if target is None:
            helper.warning("Aborted; nothing was installed.")
            return

        install_schema(
            staging=staging,
            destination=target,
            overlay=overlay,
            fingerprint=fingerprint,
        )
        helper.success(
            f"Generated and installed {overlay.schemaName} ({fingerprint[:12]})."
        )
        helper.info(f"Installed at {target}")
    finally:
        shutil.rmtree(work_root, ignore_errors=True)
