import typer

from dotools.init_app.app import get_init_app
from dotools.openspec.app import get_openspec_app
from dotools.sdk import init_main_app


def main() -> None:
    app: typer.Typer = init_main_app()
    app.add_typer(get_init_app())
    app.add_typer(get_openspec_app())
    app()


if __name__ == "__main__":
    main()
