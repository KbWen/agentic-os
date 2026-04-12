"""Regression test: trigger-registry.yaml MUST be valid pure YAML.

Uses the dependency-free _yaml_loader so these tests run in CI without PyYAML.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / ".agentcortex" / "metadata" / "trigger-registry.yaml"

# Make _yaml_loader importable
sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))
from _yaml_loader import load_data


class TriggerRegistryFormatTests(unittest.TestCase):
    def test_file_is_valid_yaml_not_json(self) -> None:
        """The registry MUST NOT parse as JSON (we migrated to pure YAML)."""
        text = REGISTRY_PATH.read_text(encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError, msg="File should not be valid JSON"):
            json.loads(text)

    def test_yaml_parses_successfully(self) -> None:
        """The registry MUST parse via load_data (PyYAML or built-in fallback)."""
        data = load_data(REGISTRY_PATH)
        self.assertIsInstance(data, dict)
        self.assertIn("version", data)
        self.assertIn("entries", data)
        self.assertIsInstance(data["entries"], list)

    def test_all_entries_have_required_fields(self) -> None:
        """Every entry MUST have the required field set."""
        data = load_data(REGISTRY_PATH)
        required = {
            "id", "kind", "canonical_ref", "platforms", "phase_scope",
            "trigger_priority", "detect_by", "load_policy", "cost_type",
            "cost_risk", "runtime_anchor", "block_if_missed", "fallback_behavior",
        }
        for entry in data["entries"]:
            missing = required - set(entry)
            self.assertFalse(missing, f"{entry.get('id', '?')}: missing {sorted(missing)}")

    def test_entry_count_matches_expected(self) -> None:
        """Guard against accidental entry loss during format migration."""
        data = load_data(REGISTRY_PATH)
        self.assertEqual(len(data["entries"]), 20, "Expected 20 trigger entries")

    def test_detect_by_fields_are_lists(self) -> None:
        """detect_by sub-fields that should be lists MUST be lists."""
        data = load_data(REGISTRY_PATH)
        list_fields = ["classification", "intent_patterns", "scope_signals",
                       "failure_signals", "phase_conditions"]
        for entry in data["entries"]:
            for field in list_fields:
                value = entry["detect_by"].get(field, [])
                self.assertIsInstance(
                    value, list,
                    f"{entry['id']}.detect_by.{field} should be list, got {type(value).__name__}"
                )


if __name__ == "__main__":
    unittest.main()
