"""Filesystem helpers for hashing and diffing schema trees."""

from __future__ import annotations

import difflib
import hashlib
from pathlib import Path

from dotools.openspec.errors import SchemaGenerationError


def _iter_entries(root: Path) -> list[Path]:
    """Return every path under ``root`` in stable relative-path order."""
    return sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix())


def hash_tree(root: Path) -> str:
    """Return a deterministic SHA-256 digest of every file under ``root``."""
    digest = hashlib.sha256()
    for path in _iter_entries(root):
        if path.is_symlink():
            raise SchemaGenerationError(
                f"Refusing symlink in upstream schema tree: {path}"
            )
        if path.is_file():
            relative = path.relative_to(root).as_posix().encode()
            digest.update(relative + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def read_tree(root: Path) -> dict[str, str]:
    """Map relative POSIX paths to file contents, skipping symlinks."""
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_text(
            encoding="utf-8", errors="replace"
        )
        for path in _iter_entries(root)
        if path.is_file() and not path.is_symlink()
    }


def diff_trees(original: Path, generated: Path) -> str:
    """Return a unified diff between two directory trees."""
    original_files = read_tree(original)
    generated_files = read_tree(generated)
    chunks: list[str] = []
    for name in sorted(original_files.keys() | generated_files.keys()):
        before = original_files.get(name, "")
        after = generated_files.get(name, "")
        if before == after:
            continue
        chunks.extend(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"original/{name}",
                tofile=f"generated/{name}",
            )
        )
    return "".join(chunks)
