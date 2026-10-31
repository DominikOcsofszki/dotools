"""Building a patched staging copy of the upstream schema."""

from __future__ import annotations

import shutil
from pathlib import Path

from dotools.openspec.errors import SchemaGenerationError
from dotools.openspec.overlay import Overlay
from dotools.openspec.schema_patch import patch_schema

SCHEMA_FILE = "schema.yaml"
README_FILE = "README.md"
TEMPLATES_DIR = "templates"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_staging(source_dir: Path, staging: Path, overlay: Overlay) -> Path:
    """Copy ``source_dir`` to ``staging`` and apply the overlay in place."""
    shutil.copytree(source_dir, staging)

    schema_path = staging / SCHEMA_FILE
    try:
        schema_text = schema_path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise SchemaGenerationError(
            f"Upstream schema is missing {SCHEMA_FILE}: {source_dir}"
        ) from error
    _write_text(schema_path, patch_schema(schema_text, overlay))

    _write_text(
        staging / TEMPLATES_DIR / overlay.expectedTaskArtifact.template,
        overlay.taskTemplate,
    )
    _write_text(staging / README_FILE, overlay.readme)
    return staging
