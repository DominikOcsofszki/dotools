"""Loading and validation of the schema customization overlay."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from dotools.openspec.errors import SchemaGenerationError

DEFAULT_OVERLAY_PATH = Path(__file__).with_name("overlay.yaml")

SUPPORTED_OVERLAY_VERSION = 1
SUPPORTED_UPSTREAM_SCHEMA = "spec-driven"


class TaskArtifact(BaseModel):
    """The upstream tasks artifact the overlay replaces."""

    model_config = ConfigDict(extra="forbid")

    id: str
    generates: str
    template: str


class Overlay(BaseModel):
    """A validated customization overlay."""

    model_config = ConfigDict(extra="forbid")

    version: int
    upstreamSchema: str
    schemaName: str
    expectedTaskArtifact: TaskArtifact
    taskTemplate: str
    applyInstruction: str
    readme: str

    @field_validator("version")
    @classmethod
    def _check_version(cls, value: int) -> int:
        if value != SUPPORTED_OVERLAY_VERSION:
            raise ValueError(
                f"unsupported overlay version {value}; "
                f"expected {SUPPORTED_OVERLAY_VERSION}"
            )
        return value

    @field_validator("upstreamSchema")
    @classmethod
    def _check_upstream_schema(cls, value: str) -> str:
        if value != SUPPORTED_UPSTREAM_SCHEMA:
            raise ValueError(
                f"unsupported upstream schema {value!r}; "
                f"expected {SUPPORTED_UPSTREAM_SCHEMA!r}"
            )
        return value

    @field_validator("schemaName")
    @classmethod
    def _check_schema_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("schemaName must not be empty")
        return value

    def fingerprint_payload(self) -> dict[str, Any]:
        """Return a stable, JSON-serializable representation for hashing."""
        return self.model_dump(mode="json")


def load_overlay(path: Path) -> Overlay:
    """Read, parse and validate an overlay file."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise SchemaGenerationError(f"Overlay not found: {path}") from error
    except OSError as error:
        raise SchemaGenerationError(f"Could not read overlay {path}: {error}") from error

    try:
        document = yaml.safe_load(raw)
    except yaml.YAMLError as error:
        raise SchemaGenerationError(f"Overlay is not valid YAML: {path}") from error

    if not isinstance(document, dict):
        raise SchemaGenerationError(f"Overlay must be a YAML mapping: {path}")

    try:
        return Overlay.model_validate(document)
    except ValidationError as error:
        raise SchemaGenerationError(
            f"Unsupported or invalid customization overlay ({path}):\n"
            f"{_format_validation_errors(error)}"
        ) from error


def _format_validation_errors(error: ValidationError) -> str:
    """Render validation issues as one indented line each."""
    lines: list[str] = []
    for issue in error.errors():
        location = ".".join(str(part) for part in issue["loc"]) or "<root>"
        lines.append(f"  - {location}: {issue['msg']}")
    return "\n".join(lines)
