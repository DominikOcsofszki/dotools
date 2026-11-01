from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from dotools.init_app.gitignore import create_gitignore
from dotools.init_app.init_basesettings_from_env import create_settings
from dotools.openspec.generate_schema import generate_schema
from dotools.openspec.task_ownership import validate_task_ownership
from dotools.sdk import AppConfig


def build_server() -> FastMCP:
    server = FastMCP("dotools")

    @server.tool(name="init-basesettings", tags={"cli"})
    def init_basesettings(env_vars: list[str]) -> str:
        """Generate base settings from environment variable names."""
        if create_settings(env_vars, deps=AppConfig()):
            return "Settings module created."
        return "Settings generation declined; no file was written."

    @server.tool(name="init-gitignore", tags={"cli"})
    def init_gitignore() -> str:
        """Create a repository .gitignore template."""
        if create_gitignore(deps=AppConfig()):
            return "Gitignore file created."
        return "Gitignore creation declined; no file was written."

    @server.tool(name="openspec-generate-schema", tags={"cli"})
    def openspec_generate_schema(
        dest: str = "",
        overlay: str = "",
        force: bool = False,
        yes: bool = False,
        check: bool = False,
    ) -> str:
        """Generate or check the customized OpenSpec schema."""
        generate_schema(
            deps=AppConfig(),
            dest=Path(dest) if dest else None,
            overlay_path=Path(overlay) if overlay else None,
            force=force,
            yes=yes,
            check=check,
        )
        return "OpenSpec schema command completed."

    @server.tool(name="openspec-validate-tasks", tags={"cli"})
    def openspec_validate_tasks(path: str) -> str:
        """Validate task ownership paths in an OpenSpec tasks file."""
        task_path = Path(path)
        problems = validate_task_ownership(task_path)
        if problems:
            raise ValueError("\n".join(problems))
        return f"Task ownership is valid: {task_path}"

    return server
