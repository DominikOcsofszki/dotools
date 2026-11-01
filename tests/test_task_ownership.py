import tempfile
import unittest
from pathlib import Path

from dotools.openspec.errors import SchemaGenerationError
from dotools.openspec.task_ownership import validate_task_ownership


class TaskOwnershipTests(unittest.TestCase):
    def _validate(self, content: str) -> list[str]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tasks.md"
            path.write_text(content, encoding="utf-8")
            return validate_task_ownership(path)

    def test_disjoint_workstreams_are_valid(self):
        problems = self._validate(
            """\
## 1. First batch
- [ ] 1.1 Implement feature - verify test passes
  - paths: `src/feature.py`, `tests/test_feature.py`
- [ ] 1.2 Document feature - verify docs build
  - paths: `docs/feature.md`
"""
        )

        self.assertEqual([], problems)

    def test_parent_and_child_paths_overlap(self):
        problems = self._validate(
            """\
## 1. First batch
- [ ] 1.1 Own source tree - verify tests pass
  - paths: `src`
- [ ] 1.2 Own one source file - verify behavior
  - paths: `src/feature.py`
"""
        )

        self.assertEqual(1, len(problems))
        self.assertIn("overlaps", problems[0])

    def test_same_path_is_allowed_in_separate_batches(self):
        problems = self._validate(
            """\
## 1. First batch
- [ ] 1.1 Implement feature — verify test passes
  - paths: `src/feature.py`
## 2. Follow-up batch
- [ ] 2.1 Update feature — verify test passes
  - paths: `src/feature.py`
"""
        )

        self.assertEqual([], problems)

    def test_every_task_requires_ownership_declaration(self):
        with self.assertRaisesRegex(SchemaGenerationError, "exactly one"):
            self._validate(
                """\
## 1. First batch
- [ ] 1.1 Implement feature
"""
            )


if __name__ == "__main__":
    unittest.main()
