from pathlib import Path
from logging import Logger, getLogger

from pydantic import BaseModel, ConfigDict, Field
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.theme import Theme
from rich.tree import Tree


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

    def ask_text_to_path(self, path: Path, text: str) -> bool:
        self.console.print(f"{text}")
        if not self.confirm.ask(f"write to {path}?"):
            return False
        if not path.parent.exists():
            path.parent.mkdir(exist_ok=True, parents=True)
            self.console.print(f"Created {path.parent}")
        path.write_text(text)
        self.console.print(f"Created {path}")
        return True


class AppServices(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    console: ConsoleServices = Field(default_factory=ConsoleServices)


class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    services: AppServices = Field(default_factory=AppServices)

    @property
    def helper(self) -> ConsoleServices:
        return self.services.console
