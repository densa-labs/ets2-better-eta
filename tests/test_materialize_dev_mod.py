from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.materialize_dev_mod import (
    MaterializationError,
    load_experiment,
    manifest,
    materialize,
)


SYNTHETIC_SOURCE = b'''SiiNunit
{
map_data : .map.data {
    road_color: 0xFF000000
    # A synthetic fixture, not SCS data.
    navigation_city_penalty: 3.0
}
}
'''


class MaterializeDevModTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "map_data.sii"
        self.source.write_bytes(SYNTHETIC_SOURCE)
        self.source_hash = hashlib.sha256(SYNTHETIC_SOURCE).hexdigest()
        self.output_root = self.root / "build"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def spec(
        self,
        name: str = "low",
        value: str = "0.50",
        expected_hash: str | None = None,
    ) -> Path:
        path = self.root / f"{name}.json"
        path.write_text(
            json.dumps(
                {
                    "profile": name,
                    "display_name": f"Synthetic {name}",
                    "expected_source_sha256": expected_hash or self.source_hash,
                    "assignments": [
                        {
                            "field": "navigation_time_road_max_speed_usage",
                            "value": value,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_known_source_hash_is_accepted_and_field_inserted_once(self) -> None:
        result = materialize(self.source, self.spec(), self.output_root)
        generated = result.output_path.read_bytes()
        assignment = b"navigation_time_road_max_speed_usage: 0.50"
        self.assertEqual(generated.count(assignment), 1)
        self.assertEqual(result.source_hash, self.source_hash)
        self.assertEqual(result.output_hash, hashlib.sha256(generated).hexdigest())

    def test_manifest_uses_valid_short_unit_identifier(self) -> None:
        experiment_path = self.spec()
        generated_manifest = manifest(load_experiment(experiment_path))
        self.assertIn(b"mod_package : .b_eta_m2\n", generated_manifest)
        self.assertNotIn(b".better_eta_m2", generated_manifest)

    def test_unexpected_source_hash_is_rejected_by_default(self) -> None:
        with self.assertRaisesRegex(MaterializationError, "unexpected stock source SHA-256"):
            materialize(self.source, self.spec(expected_hash="0" * 64), self.output_root)

    def test_explicit_development_override_allows_unexpected_hash(self) -> None:
        result = materialize(
            self.source,
            self.spec(expected_hash="0" * 64),
            self.output_root,
            allow_unexpected_source=True,
        )
        self.assertTrue(result.output_path.is_file())

    def test_existing_assignment_is_rejected(self) -> None:
        self.source.write_bytes(
            SYNTHETIC_SOURCE.replace(
                b"    navigation_city_penalty: 3.0\n",
                b"    navigation_time_road_max_speed_usage: 0.75\n",
            )
        )
        with self.assertRaisesRegex(MaterializationError, "source already assigns"):
            materialize(
                self.source,
                self.spec(expected_hash=hashlib.sha256(self.source.read_bytes()).hexdigest()),
                self.output_root,
            )

    def test_comment_mention_is_not_an_existing_assignment(self) -> None:
        source = SYNTHETIC_SOURCE.replace(
            b"    # A synthetic fixture, not SCS data.\n",
            b"    # navigation_time_road_max_speed_usage: 0.75\n",
        )
        self.source.write_bytes(source)
        result = materialize(
            self.source,
            self.spec(expected_hash=hashlib.sha256(source).hexdigest()),
            self.output_root,
        )
        self.assertEqual(
            result.output_path.read_bytes().count(b"navigation_time_road_max_speed_usage:"),
            2,
        )

    def test_low_and_high_outputs_are_deterministic_and_distinct(self) -> None:
        low_spec = self.spec("low", "0.50")
        high_spec = self.spec("high", "1.00")
        low_first = materialize(self.source, low_spec, self.output_root)
        high_first = materialize(self.source, high_spec, self.output_root)
        low_second = materialize(self.source, low_spec, self.output_root)
        high_second = materialize(self.source, high_spec, self.output_root)
        self.assertEqual(low_first.output_hash, low_second.output_hash)
        self.assertEqual(high_first.output_hash, high_second.output_hash)
        self.assertNotEqual(low_first.output_hash, high_first.output_hash)

    def test_source_is_preserved_outside_exact_inserted_block(self) -> None:
        result = materialize(self.source, self.spec(), self.output_root)
        inserted = (
            b"\t# Better ETA experimental profile: low\n"
            b"\tnavigation_time_road_max_speed_usage: 0.50\n"
        )
        generated = result.output_path.read_bytes()
        self.assertEqual(generated.count(inserted), 1)
        self.assertEqual(generated.replace(inserted, b""), SYNTHETIC_SOURCE)

    def test_missing_map_data_unit_is_rejected(self) -> None:
        source = b"SiiNunit\n{\nother_data : .other.data {\n}\n}\n"
        self.source.write_bytes(source)
        with self.assertRaisesRegex(MaterializationError, "found 0"):
            materialize(
                self.source,
                self.spec(expected_hash=hashlib.sha256(source).hexdigest()),
                self.output_root,
            )


if __name__ == "__main__":
    unittest.main()
