import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp_plugin_gateway.cli import build_cli
from mcp_plugin_gateway.registry import build_registry
from mcp_plugin_gateway.server import build_default_server, is_mcp_visible
from typer.testing import CliRunner

from dotools.openspec.errors import SchemaGenerationError
from dotools_cli_plugin import build_server


class PluginTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = build_server()

    async def test_tools_are_cli_only_and_have_stable_names(self):
        tools = await self.server.list_tools()

        self.assertEqual(
            {
                "init-basesettings",
                "init-gitignore",
                "openspec-generate-schema",
                "openspec-validate-tasks",
            },
            {tool.name for tool in tools},
        )
        self.assertTrue(all(tool.tags == {"cli"} for tool in tools))
        self.assertTrue(all(not is_mcp_visible(tool) for tool in tools))

    async def test_gateway_mcp_server_hides_cli_only_tools(self):
        gateway_server = build_default_server(build_registry())

        self.assertEqual([], await gateway_server.list_tools())

    async def test_init_basesettings_reports_create_and_decline(self):
        with patch("dotools_cli_plugin.create_settings", return_value=True):
            async with Client(self.server) as client:
                created = await client.call_tool(
                    "init-basesettings", {"env_vars": ["API_KEY", "TOKEN"]}
                )
        self.assertIn("created", created.content[0].text)

        with patch("dotools_cli_plugin.create_settings", return_value=False):
            async with Client(self.server) as client:
                declined = await client.call_tool(
                    "init-basesettings", {"env_vars": ["API_KEY"]}
                )
        self.assertIn("declined", declined.content[0].text)
        self.assertIn("no file was written", declined.content[0].text)

    async def test_init_gitignore_reports_create_and_decline(self):
        with patch("dotools_cli_plugin.create_gitignore", return_value=True):
            async with Client(self.server) as client:
                created = await client.call_tool("init-gitignore", {})
        self.assertIn("created", created.content[0].text)

        with patch("dotools_cli_plugin.create_gitignore", return_value=False):
            async with Client(self.server) as client:
                declined = await client.call_tool("init-gitignore", {})
        self.assertIn("declined", declined.content[0].text)
        self.assertIn("no file was written", declined.content[0].text)

    async def test_schema_tool_converts_cli_values_and_preserves_defaults(self):
        with patch("dotools_cli_plugin.generate_schema") as generate:
            async with Client(self.server) as client:
                result = await client.call_tool(
                    "openspec-generate-schema",
                    {"dest": "/tmp/schema", "overlay": "", "force": True},
                )

        kwargs = generate.call_args.kwargs
        self.assertEqual(Path("/tmp/schema"), kwargs["dest"])
        self.assertIsNone(kwargs["overlay_path"])
        self.assertTrue(kwargs["force"])
        self.assertFalse(kwargs["yes"])
        self.assertFalse(kwargs["check"])
        self.assertIn("completed", result.content[0].text)

    async def test_schema_failures_are_reported(self):
        with patch(
            "dotools_cli_plugin.generate_schema",
            side_effect=SchemaGenerationError("schema failure"),
        ):
            async with Client(self.server) as client:
                with self.assertRaisesRegex(ToolError, "schema failure"):
                    await client.call_tool(
                        "openspec-generate-schema", {"dest": "", "overlay": ""}
                    )

    async def test_validate_tasks_accepts_valid_file_and_reports_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            valid = Path(temporary) / "valid.md"
            valid.write_text(
                "## 1. Batch\n- [ ] 1.1 Task\n  - paths: `src/feature.py`\n",
                encoding="utf-8",
            )
            async with Client(self.server) as client:
                result = await client.call_tool(
                    "openspec-validate-tasks", {"path": str(valid)}
                )
            self.assertIn("Task ownership is valid", result.content[0].text)

            invalid = Path(temporary) / "invalid.md"
            invalid.write_text(
                "## 1. Batch\n- [ ] 1.1 Task\n  - paths: `src`\n"
                "- [ ] 1.2 Another task\n  - paths: `src/feature.py`\n",
                encoding="utf-8",
            )
            async with Client(self.server) as client:
                with self.assertRaisesRegex(ToolError, "overlaps"):
                    await client.call_tool(
                        "openspec-validate-tasks", {"path": str(invalid)}
                    )


class GatewayCliMappingTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.app = build_cli(build_registry())

    def test_list_argument_maps_to_positional_values(self):
        with patch("dotools_cli_plugin.create_settings") as create_settings:
            result = self.runner.invoke(
                self.app,
                ["dotools", "init-basesettings", "API_KEY", "TOKEN"],
            )

        self.assertEqual(0, result.exit_code, result.output)
        self.assertEqual(["API_KEY", "TOKEN"], create_settings.call_args.args[0])

    def test_optional_paths_and_boolean_flags_map_correctly(self):
        with patch("dotools_cli_plugin.generate_schema") as generate:
            result = self.runner.invoke(
                self.app,
                [
                    "dotools",
                    "openspec-generate-schema",
                    "--dest",
                    "/tmp/schema",
                    "--force",
                    "--yes",
                    "--check",
                ],
            )

        self.assertEqual(0, result.exit_code, result.output)
        kwargs = generate.call_args.kwargs
        self.assertEqual(Path("/tmp/schema"), kwargs["dest"])
        self.assertIsNone(kwargs["overlay_path"])
        self.assertTrue(kwargs["force"])
        self.assertTrue(kwargs["yes"])
        self.assertTrue(kwargs["check"])

    def test_task_path_maps_to_required_argument(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tasks.md"
            path.write_text(
                "## 1. Batch\n- [ ] 1.1 Task\n  - paths: `src/feature.py`\n",
                encoding="utf-8",
            )
            result = self.runner.invoke(
                self.app,
                ["dotools", "openspec-validate-tasks", str(path)],
            )

        self.assertEqual(0, result.exit_code, result.output)
        self.assertIn("Task ownership is valid", result.output)

    def test_invalid_operation_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tasks.md"
            path.write_text(
                "## 1. Batch\n- [ ] 1.1 Task\n  - paths: `src`\n"
                "- [ ] 1.2 Another task\n  - paths: `src/feature.py`\n",
                encoding="utf-8",
            )
            result = self.runner.invoke(
                self.app,
                ["dotools", "openspec-validate-tasks", str(path)],
            )

        self.assertNotEqual(0, result.exit_code)
        self.assertIn("overlaps", result.output)


if __name__ == "__main__":
    unittest.main()
