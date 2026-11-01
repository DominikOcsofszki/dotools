# dotools

## CLI setup

From the repository root, with this package checked out at `dotools/`, install
the project and its locked dependencies with uv:

```bash
uv sync --project dotools
```

The MCP Plugin Gateway discovers the installed `dotools` plugin and builds its
CLI from the plugin's FastMCP tool schemas. The gateway dependency is pinned to
release tag `0.0.1` in `pyproject.toml` and `uv.lock`.

Run utility commands from the repository root so relative paths and OpenSpec
output destinations resolve against the repository. If the package checkout is
elsewhere, replace `dotools` in `--project dotools` with its path.

## Gateway-generated CLI

List the plugin commands and inspect their arguments:

```bash
uv run --project dotools mcp-plugin-gateway --help
uv run --project dotools mcp-plugin-gateway dotools --help
```

The four utility commands are:

```bash
uv run --project dotools mcp-plugin-gateway dotools init-basesettings API_KEY DATABASE_URL
uv run --project dotools mcp-plugin-gateway dotools init-gitignore
uv run --project dotools mcp-plugin-gateway dotools openspec-generate-schema --check
uv run --project dotools mcp-plugin-gateway dotools openspec-validate-tasks tasks.md
```

`openspec-generate-schema` also accepts `--dest PATH`, `--overlay PATH`,
`--force`, and `--yes`. The settings command takes one or more environment
variable names. The schema generator uses its default destination and overlay
when those options are omitted.

These plugin tools are tagged for the CLI surface only. They are not exposed as
tools to MCP clients, and using these commands does not require starting an MCP
server or configuring an MCP client.

## Existing `dotools` command

The existing Typer command remains available as a compatibility alias:

```bash
uv run --project dotools dotools init basesettings API_KEY DATABASE_URL
uv run --project dotools dotools init gitignore
uv run --project dotools dotools openspec generate-schema --check
uv run --project dotools dotools openspec validate-tasks tasks.md
```
