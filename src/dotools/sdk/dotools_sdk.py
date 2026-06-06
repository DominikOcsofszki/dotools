from pathlib import Path
import logging
from functools import cache
from importlib.metadata import version
from logging import Logger, getLogger

import typer
from pydantic import BaseModel, ConfigDict, Field
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.theme import Theme
from rich.tree import Tree


def verbose_option() -> int:
    def callback(verbose: int) -> int:
        level = {
            0: logging.WARNING,
            1: logging.INFO,
            2: logging.DEBUG,
        }.get(verbose, logging.DEBUG)

        logging.basicConfig(
            level=level,
            format="%(message)s",
            handlers=[RichHandler()],
        )

        return verbose

    return typer.Option(
        0,
        "-v",
        "--verbose",
        count=True,
        callback=callback,
        help="Increase logging verbosity (-v=INFO, -vv=DEBUG).",
    )


def create_console() -> Console:
    return Console(
        theme=Theme(
            {
                "success": "green",
                "warning": "yellow",
                "error": "bold red",
                "info": "cyan",
            }
        )
    )


def create_logger() -> Logger:
    return getLogger("dotools")


class ConsoleServices(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    console: Console = Field(default_factory=create_console)
    logger: Logger = Field(default_factory=create_logger)
    progress: type[Progress] = Progress
    prompt: type[Prompt] = Prompt
    confirm: type[Confirm] = Confirm
    table: type[Table] = Table
    tree: type[Tree] = Tree

    def success(self, message: str) -> None:
        self.console.print(message, style="success")

    def info(self, message: str) -> None:
        self.console.print(message, style="info")

    def warning(self, message: str) -> None:
        self.console.print(message, style="warning")

    def error(self, message: str) -> None:
        self.console.print(message, style="error")

    def rule(self, title: str) -> None:
        self.console.rule(title)

    def ask_text_to_path(self, path: Path, text: str):
        self.console.print(f"{text}")
        if self.confirm.ask(f"write to {path}?"):
            if not path.parent.exists():
                self.console.print(f"Created {path.parent}")
                path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text(text)
            self.console.print(f"Created {path}")


class AppServices(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    console: ConsoleServices = Field(default_factory=ConsoleServices)


class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    services: AppServices = Field(default_factory=AppServices)

    @property
    def helper(self) -> ConsoleServices:
        return self.services.console


def version_option(package: str):
    def callback(value: bool) -> None:
        if value:
            typer.echo(version(package))
            raise typer.Exit()

    return typer.Option(
        False,
        "--version",
        callback=callback,
        is_eager=True,
    )


def _init_app_config() -> AppConfig:
    return AppConfig()


def init_app(
    name: str,
    help: str,
    *,
    _app_config: AppConfig | None = None,
) -> typer.Typer:
    app = typer.Typer(
        name=name,
        help=help,
        no_args_is_help=True,
    )

    @app.callback()
    def main(
        ctx: typer.Context,
        version_: bool = version_option("dotools"),
        verbose: int = verbose_option(),
    ) -> None:
        if _app_config:
            ctx.obj = _app_config

    return app


def _init_main_app(app_config) -> typer.Typer:
    app = init_app(
        name="dotools",
        help="Small developer utilities",
        _app_config=app_config,
    )
    return app


@cache
def init_main_app() -> typer.Typer:
    app_config = _init_app_config()
    app = _init_main_app(app_config)
    return app


def get_app_config(ctx: typer.Context) -> AppConfig:
    app_config: AppConfig = ctx.obj
    return app_config
