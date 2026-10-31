from pathlib import Path

import typer

from dotools.openspec.generate_schema import (
    DEFAULT_OVERLAY_PATH,
    SchemaGenerationError,
    generate_schema,
)
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
    ) -> None:
        app_config = get_app_config(ctx)
        try:
            generate_schema(
                deps=app_config,
                dest=dest,
                overlay_path=overlay,
                force=force,
                yes=yes,
            )
        except SchemaGenerationError as error:
            app_config.helper.error(f"generate-schema: {error}")
            raise typer.Exit(code=1) from error

    return app
