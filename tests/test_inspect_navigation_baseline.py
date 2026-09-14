from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.inspect_navigation_baseline import EXPECTED_FIELDS, inspect, render


class InspectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "def").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    @staticmethod
    def expected_fields(skip: str | None = None) -> str:
        return "\n".join(
            f"  {name}: {index}.00" for index, name in enumerate(EXPECTED_FIELDS, 1) if name != skip
        )

    def test_seven_expected_fields_and_exact_text_values(self) -> None:
        entry = self.write(
            "def/map_data.sii",
            "SiiNunit\n{\n" + self.expected_fields() + "\n}\n",
        )
        result = inspect(entry)
        self.assertEqual([field.name for field in result.fields], list(EXPECTED_FIELDS))
        self.assertEqual(result.fields[0].value, "1.00")
        self.assertIn("MISSING EXPECTED FIELDS\n(none)", render(result))

    def test_missing_expected_and_unexpected_time_field(self) -> None:
        missing = EXPECTED_FIELDS[2]
        entry = self.write(
            "def/map_data.sii",
            self.expected_fields(skip=missing) + "\n navigation_time_future_field: 9e-1 // note\n",
        )
        report = render(inspect(entry))
        self.assertIn(f"{missing}: MISSING", report)
        self.assertIn("ADDITIONAL navigation_time_* FIELDS\nnavigation_time_future_field", report)
        self.assertIn("navigation_time_future_field: 9e-1", report)

    def test_recursive_includes_missing_include_cycle_and_comments(self) -> None:
        entry = self.write(
            "def/map_data.sii",
            '@include "navigation/one.sii"\n@include "missing.sii"\n'
            '// navigation_fake: 1\n/* navigation_blocked: 2 */\n',
        )
        self.write(
            "def/navigation/one.sii",
            '@include "two.sii"\n navigation_route_weight: 2\n',
        )
        self.write(
            "def/navigation/two.sii",
            '@include "../map_data.sii"\n navigation_time_stop_wait_duration: 3.500\n',
        )
        result = inspect(entry)
        report = render(result)
        self.assertEqual([include.status for include in result.includes], ["FOUND", "FOUND", "CYCLE", "MISSING"])
        self.assertIn("navigation_time_stop_wait_duration: 3.500", report)
        self.assertNotIn("navigation_fake:", report)
        self.assertNotIn("navigation_blocked:", report)

    def test_outside_root_include_is_not_followed(self) -> None:
        entry = self.write("def/map_data.sii", '@include "../../outside.sii"\n')
        result = inspect(entry)
        self.assertEqual(result.includes[0].status, "OUTSIDE_ROOT")
        self.assertEqual(result.files, [entry.resolve()])

    def test_def_directory_resolves_game_root_relative_include(self) -> None:
        self.write("def/map_data.sii", '@include "/def/navigation.sii"\n')
        included = self.write("def/navigation.sii", "navigation_time_stop_wait_duration: 4\n")
        result = inspect(self.root / "def")
        self.assertEqual(result.root, self.root.resolve())
        self.assertEqual(result.files[1], included.resolve())
        self.assertEqual(result.includes[0].status, "FOUND")

    def test_output_is_deterministic(self) -> None:
        entry = self.write("def/map_data.sii", self.expected_fields() + "\n")
        self.assertEqual(render(inspect(entry)), render(inspect(entry)))


if __name__ == "__main__":
    unittest.main()
