from pathlib import Path
from dotools.sdk import AppConfig


def create_gitignore(*, deps: AppConfig) -> None:
    code = """
# Byte-compiled / cache
__pycache__/
*.py[cod]
*.pyo

# Virtual environments
.venv/

# Python tooling
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# IDEs
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db

# Environment variables
.env
.env.*

# Build artifacts
build/
dist/
*.egg-info/

# uv
.python-version

"""

    path = Path("./__.gitignore")

    deps.helper.ask_text_to_path(path, code)
