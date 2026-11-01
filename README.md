# dotools

## Install

From the repository root, install the core package and every workspace member:

```bash
uv sync --project dotools --all-packages
```

`--all-packages` is required so uv installs the `plugins/dotools-cli` workspace
member alongside the core package. The MCP Plugin Gateway discovers the
installed plugin and builds its CLI from the FastMCP tool schemas. The gateway
dependency is pinned to release tag `0.0.1` in `pyproject.toml` and `uv.lock`.

Run utility commands from the repository root so relative paths and OpenSpec
output destinations resolve against the repository.

## Gateway-generated CLI

List the plugin commands and inspect their arguments:

```bash
uv run --project dotools --all-packages mcp-plugin-gateway --help
uv run --project dotools --all-packages mcp-plugin-gateway dotools --help
```

The four utility commands are:

```bash
uv run --project dotools --all-packages mcp-plugin-gateway dotools init-basesettings API_KEY DATABASE_URL
uv run --project dotools --all-packages mcp-plugin-gateway dotools init-gitignore
uv run --project dotools --all-packages mcp-plugin-gateway dotools openspec-generate-schema --check
uv run --project dotools --all-packages mcp-plugin-gateway dotools openspec-validate-tasks tasks.md
```

`openspec-generate-schema` also accepts `--dest PATH`, `--overlay PATH`,
`--force`, and `--yes`. The settings command takes one or more environment
variable names. The schema generator uses its default destination and overlay
when those options are omitted.

These plugin tools are tagged for the CLI surface only. They are not exposed as
tools to MCP clients, and using these commands does not require starting an MCP
server or configuring an MCP client.

## Migrate from the `dotools` CLI

The legacy `dotools` executable is no longer installed. Use these gateway
commands instead:

| Former command | Gateway command |
| --- | --- |
| `dotools init basesettings VAR...` | `mcp-plugin-gateway dotools init-basesettings VAR...` |
| `dotools init gitignore` | `mcp-plugin-gateway dotools init-gitignore` |
| `dotools openspec generate-schema [OPTIONS]` | `mcp-plugin-gateway dotools openspec-generate-schema [OPTIONS]` |
| `dotools openspec validate-tasks PATH` | `mcp-plugin-gateway dotools openspec-validate-tasks PATH` |
