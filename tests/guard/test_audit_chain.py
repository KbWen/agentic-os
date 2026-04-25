"""Tests for ADR-003 hash-chained audit log helper + validator.

Spec: docs/specs/hash-chained-audit-log.md (forthcoming)
ADR: docs/adr/ADR-003-hash-chained-audit-log.md

Includes the chaos-style adversarial test: tamper a line, verify the
validator catches it. This is the regression test for Lesson L4 (honor
system → external observer).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))

import append_chain_entry as ace  # noqa: E402
import check_audit_chain as cac  # noqa: E402


class TestCanonicalAndHash(unittest.TestCase):
    def test_canonical_excludes_prev_sha(self) -> None:
        with_chain = {"a": 1, "b": 2, "prev_sha": "abcd1234"}
        without = {"a": 1, "b": 2}
        self.assertEqual(ace.canonical(with_chain), ace.canonical(without))

    def test_chain_sha_deterministic(self) -> None:
        e = {"a": 1}
        self.assertEqual(ace.chain_sha(e), ace.chain_sha(e))

    def test_chain_sha_length(self) -> None:
        self.assertEqual(len(ace.chain_sha({"a": 1})), ace.SHA_LEN)


class TestAppend(unittest.TestCase):
    def test_genesis(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            written = ace.append_chained(path, {"key": "value"})
            self.assertEqual(written["prev_sha"], ace.GENESIS)
            line = path.read_text(encoding="utf-8").strip()
            obj = json.loads(line)
            self.assertEqual(obj, written)

    def test_chained(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            first = ace.append_chained(path, {"i": 1})
            second = ace.append_chained(path, {"i": 2})
            self.assertEqual(first["prev_sha"], ace.GENESIS)
            self.assertEqual(second["prev_sha"], ace.chain_sha(first))

    def test_rejects_explicit_prev_sha(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            with self.assertRaises(ValueError):
                ace.append_chained(path, {"i": 1, "prev_sha": "manual"})


class TestMigrate(unittest.TestCase):
    def test_assigns_chain_to_existing_entries(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            # Pre-existing un-chained entries
            path.write_text(
                json.dumps({"i": 1}, sort_keys=True) + "\n"
                + json.dumps({"i": 2}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            n = ace.migrate(path)
            self.assertEqual(n, 2)
            entries = [obj for _, obj in ace.iter_entries(path)]
            self.assertEqual(entries[0]["prev_sha"], ace.GENESIS)
            self.assertEqual(entries[1]["prev_sha"], ace.chain_sha({"i": 1}))

    def test_idempotent_when_already_chained(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            ace.append_chained(path, {"i": 1})
            ace.append_chained(path, {"i": 2})
            n_first = ace.migrate(path)
            n_second = ace.migrate(path)
            self.assertEqual(n_first, 0)
            self.assertEqual(n_second, 0)

    def test_empty_file_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            path.write_text("", encoding="utf-8")
            n = ace.migrate(path)
            self.assertEqual(n, 0)


class TestCheckChain(unittest.TestCase):
    def test_intact_chain(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            ace.append_chained(path, {"i": 1})
            ace.append_chained(path, {"i": 2})
            ace.append_chained(path, {"i": 3})
            intact, errors = cac.check_chain(path)
            self.assertTrue(intact)
            self.assertEqual(errors, [])

    def test_missing_file_intact(self) -> None:
        intact, errors = cac.check_chain(Path("/no/such/file"))
        self.assertTrue(intact)
        self.assertEqual(errors, [])

    def test_missing_prev_sha_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            path.write_text(json.dumps({"i": 1}, sort_keys=True) + "\n", encoding="utf-8")
            intact, errors = cac.check_chain(path)
            self.assertFalse(intact)
            self.assertIn("missing", errors[0])

    def test_tampered_entry_breaks_chain(self) -> None:
        """ADVERSARIAL: silently rewrite history; verify validator catches."""
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            ace.append_chained(path, {"i": 1, "decision": "good"})
            ace.append_chained(path, {"i": 2, "decision": "good"})
            ace.append_chained(path, {"i": 3, "decision": "good"})
            # Attacker rewrites the FIRST entry to alter recorded decision
            lines = path.read_text(encoding="utf-8").splitlines()
            obj0 = json.loads(lines[0])
            obj0["decision"] = "MALICIOUS-OVERWRITE"
            lines[0] = json.dumps(obj0, sort_keys=True, ensure_ascii=False)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            # Validator should see the chain break starting at line 2
            intact, errors = cac.check_chain(path)
            self.assertFalse(intact)
            self.assertEqual(len(errors), 1)
            self.assertIn("line 2", errors[0])
            self.assertIn("chain broken", errors[0])

    def test_genesis_with_wrong_prev_sha_fails(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            path.write_text(
                json.dumps({"i": 1, "prev_sha": "WRONG"}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            intact, errors = cac.check_chain(path)
            self.assertFalse(intact)
            self.assertIn("expected 'GENESIS'", errors[0])


if __name__ == "__main__":
    unittest.main()
