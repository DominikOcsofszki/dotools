"""Fingerprinting of generator inputs, used to skip redundant regeneration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from dotools.openspec.overlay import Overlay
from dotools.openspec.tree import hash_tree

_GENERATOR_SOURCE = Path(__file__).resolve()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _generator_fingerprint() -> str:
    """Hash the generator package so code changes invalidate cached output."""
    digest = hashlib.sha256()
    for path in sorted(_GENERATOR_SOURCE.parent.glob("*.py")):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def compute_fingerprint(source_dir: Path, overlay: Overlay) -> str:
    """Combine upstream tree, overlay and generator hashes into one digest."""
    overlay_fingerprint = _sha256(
        json.dumps(
            overlay.fingerprint_payload(), sort_keys=True, separators=(",", ":")
        ).encode()
    )
    return _sha256(
        "\0".join(
            (hash_tree(source_dir), overlay_fingerprint, _generator_fingerprint())
        ).encode()
    )
