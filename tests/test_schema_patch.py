import tempfile
import unittest
from pathlib import Path

from dotools.openspec.overlay import DEFAULT_OVERLAY_PATH, Overlay, load_overlay
from dotools.openspec.schema_patch import patch_schema
from dotools.openspec.staging import build_staging


UPSTREAM_SCHEMA = """\
name: spec-driven
artifacts:
  - id: tasks
    generates: tasks.md
    description: Implementation checklist
    template: tasks.md
    instruction: |
      Write a flat task list.
    requires:
      - design
apply:
  requires: [tasks]
  tracks: tasks.md
  instruction: |
    Apply one task at a time.
"""


class SchemaPatchTests(unittest.TestCase):
    def test_project_overlay_overrides_task_instruction_and_apply_instruction(self):
        overlay = load_overlay(DEFAULT_OVERLAY_PATH)

        result = patch_schema(UPSTREAM_SCHEMA, overlay)

        self.assertIn("name: parallel-task-apply", result)
        self.assertIn(
            "Create a dependency-ordered implementation plan grouped into "
            "numbered batches.",
            result,
        )
        self.assertIn("openspec-parallel-apply` skill", result)
        self.assertNotIn("Write a flat task list.", result)
        self.assertNotIn("Apply one task at a time.", result)

    def test_template_path_drift_fails_loudly(self):
        overlay = Overlay.model_validate(
            {
                "version": 2,
                "upstreamSchema": "spec-driven",
                "schemaName": "custom",
                "expectedTaskArtifact": {
                    "id": "tasks",
                    "generates": "tasks.md",
                    "template": "tasks.md",
                },
                "artifactOverrides": {
                    "tasks": {
                        "templatePath": "tasks.md",
                        "templateContent": "custom template",
                    }
                },
                "applyInstruction": "apply",
                "readme": "readme",
            }
        )
        changed_path = UPSTREAM_SCHEMA.replace(
            "template: tasks.md", "template: other.md"
        )

        with self.assertRaisesRegex(RuntimeError, "artifact paths changed"):
            patch_schema(changed_path, overlay)

    def test_build_staging_writes_each_overridden_template(self):
        overlay = load_overlay(DEFAULT_OVERLAY_PATH)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "templates").mkdir(parents=True)
            (source / "schema.yaml").write_text(UPSTREAM_SCHEMA, encoding="utf-8")
            (source / "templates" / "tasks.md").write_text(
                "upstream template", encoding="utf-8"
            )

            staging = build_staging(source, root / "staging", overlay)

            generated_template = (staging / "templates" / "tasks.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(
                overlay.artifactOverrides["tasks"].templateContent,
                generated_template,
            )


if __name__ == "__main__":
    unittest.main()
