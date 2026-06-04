import typer

from dotools.init_app import init_basesettings_from_env, gitignore
from dotools.sdk import get_app_config
from dotools.sdk.dotools_sdk import init_app


def get_init_app() -> typer.Typer:
    app: typer.Typer = init_app(name="init", help="init repo tools")

    @app.command("basesettings")
    def _(ctx: typer.Context, env_vars: list[str]):
        app_config = get_app_config(ctx)
        init_basesettings_from_env.create_settings(env_vars, deps=app_config)

    @app.command("gitignore")
    def _(ctx: typer.Context):
        app_config = get_app_config(ctx)
        gitignore.create_gitignore(deps=app_config)

    return app
