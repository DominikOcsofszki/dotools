"""Console presentation helpers for the schema generator."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from dotools.openspec.errors import SchemaGenerationError

_DIFF_STYLES = (
    (("+++", "---"), "bold"),
    (("@@",), "info"),
    (("+",), "success"),
    (("-",), "error"),
)


class Helper(Protocol):
    """The subset of ``ConsoleServices`` used by the generator."""

    console: object
    prompt: object

    def success(self, message: str) -> None: ...
    def info(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
    def rule(self, title: str) -> None: ...


def print_diff(helper: Helper, diff: str) -> None:
    """Print a unified diff with per-line styling."""
    for line in diff.splitlines():
        style = next(
            (style for prefixes, style in _DIFF_STYLES if line.startswith(prefixes)),
            None,
        )
        if style:
            helper.console.print(line, style=style)
        else:
            helper.console.print(line)


def confirm_destination(helper: Helper, default: Path) -> Path | None:
    """Ask where to install; return ``None`` when the user aborts."""
    helper.console.print()
    helper.info(f"Default destination: {default}")
    choice = helper.prompt.ask(
        "Install generated schema?",
        choices=["yes", "no", "other"],
        default="yes",
        console=helper.console,
    )
    if choice == "no":
        return None
    if choice == "other":
        raw = helper.prompt.ask(
            "Destination directory",
            default=str(default),
            console=helper.console,
        )
        return _resolve_destination(raw)
    return default


def _resolve_destination(raw: str) -> Path:
    try:
        return Path(raw).expanduser().resolve()
    except OSError as error:
        raise SchemaGenerationError(
            f"Invalid destination directory {raw!r}: {error}"
        ) from error
