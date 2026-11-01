from pathlib import Path

import typer

from dotools.openspec.generate_schema import (
    DEFAULT_OVERLAY_PATH,
    SchemaGenerationError,
    generate_schema,
)
from dotools.openspec.task_ownership import validate_task_ownership
from dotools.sdk import get_app_config
from dotools.sdk.dotools_sdk import init_app


def get_openspec_app() -> typer.Typer:
    app: typer.Typer = init_app(name="openspec", help="OpenSpec schema tools")

    @app.command("generate-schema")
    def _(
        ctx: typer.Context,
        dest: Path | None = typer.Option(
            None,
            "--dest",
            "-d",
            help="Output directory (default: ./openspec/schemas/<schema-name>).",
        ),
        overlay: Path | None = typer.Option(
            None,
            "--overlay",
            help=f"Customization overlay (default: {DEFAULT_OVERLAY_PATH.name}).",
        ),
        force: bool = typer.Option(
            False,
            "--force",
            help="Regenerate even when the fingerprint is unchanged.",
        ),
        yes: bool = typer.Option(
            False,
            "--yes",
            "-y",
            help="Skip the diff confirmation and install to the default destination.",
        ),
        check: bool = typer.Option(
            False,
            "--check",
            help="Check whether the generated schema matches the destination without writing.",
        ),
    ) -> None:
        app_config = get_app_config(ctx)
        try:
            generate_schema(
                deps=app_config,
                dest=dest,
                overlay_path=overlay,
                force=force,
                yes=yes,
                check=check,
            )
        except SchemaGenerationError as error:
            app_config.helper.error(f"generate-schema: {error}")
            raise typer.Exit(code=1) from error

    @app.command("validate-tasks")
    def _(
        ctx: typer.Context,
        path: Path = typer.Argument(..., exists=True, dir_okay=False),
    ) -> None:
        app_config = get_app_config(ctx)
        try:
            problems = validate_task_ownership(path)
        except SchemaGenerationError as error:
            app_config.helper.error(f"validate-tasks: {error}")
            raise typer.Exit(code=1) from error
        if problems:
            for problem in problems:
                app_config.helper.error(problem)
            raise typer.Exit(code=1)
        app_config.helper.success(f"Task ownership is valid: {path}")

    return app
