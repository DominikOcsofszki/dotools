"""Shared exception type for OpenSpec schema generation."""

from __future__ import annotations


class SchemaGenerationError(RuntimeError):
    """Raised when a schema cannot be generated or installed safely."""
