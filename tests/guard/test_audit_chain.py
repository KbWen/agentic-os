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

    # --- spec archive-name-collisions AC-8: one INDEX entry per archived log ---

    def test_rejects_log_already_recorded(self) -> None:
        """A second same-day ship on a reused key must not point INDEX at the first
        ship's file: the duplicate `log` is refused and nothing is written."""
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "INDEX.jsonl"
            ace.append_chained(path, {"log": "main-20261006.md", "decisions": ["ship 1"]})
            before = path.read_bytes()
            with self.assertRaises(ValueError) as ctx:
                ace.append_chained(path, {"log": "main-20261006.md", "decisions": ["ship 2"]})
            self.assertIn("--2-", str(ctx.exception))
            self.assertEqual(path.read_bytes(), before)

    def test_identical_reappend_is_a_noop(self) -> None:
        """A retried ship re-runs the same append: it is already recorded, so nothing
        is written and no rename is suggested (a rename would leave a dangling entry)."""
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "INDEX.jsonl"
            entry = {"log": "main-20261006.md", "shipped": "2026-10-06"}
            first = ace.append_chained(path, dict(entry))
            before = path.read_bytes()
            again = ace.append_chained(path, dict(entry))
            self.assertEqual(again, first)
            self.assertEqual(path.read_bytes(), before)

    def test_duplicate_collision_name_suggests_next_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "INDEX.jsonl"
            ace.append_chained(path, {"log": "main--2-20261006.md", "decisions": ["ship 2"]})
            with self.assertRaises(ValueError) as ctx:
                ace.append_chained(path, {"log": "main--2-20261006.md", "decisions": ["ship 3"]})
            self.assertIn("'main--3-20261006.md'", str(ctx.exception))

    def test_distinct_logs_and_logless_entries_still_append(self) -> None:
        """The guard keys on `log` only: a `--2-` name and repeated log-less records
        (e.g. append_lesson.py archive records) append as before."""
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "INDEX.jsonl"
            ace.append_chained(path, {"log": "main-20261006.md"})
            ace.append_chained(path, {"log": "main--2-20261006.md"})
            ace.append_chained(path, {"type": "lesson_archive"})
            ace.append_chained(path, {"type": "lesson_archive"})
            self.assertEqual(len(list(ace.iter_entries(path))), 4)
            intact, _ = cac.check_chain(path)
            self.assertTrue(intact)

    def test_cli_duplicate_log_exits_nonzero(self) -> None:
        """The path /ship actually runs: the CLI exits 1 and names the remedy."""
        import subprocess

        script = ROOT / ".agentcortex" / "tools" / "append_chain_entry.py"
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "INDEX.jsonl"

            def run(entry: dict) -> "subprocess.CompletedProcess[str]":
                cmd = [sys.executable, str(script), "append", "--path", str(path),
                       "--entry", json.dumps(entry)]
                return subprocess.run(cmd, capture_output=True, text=True,
                                      encoding="utf-8", errors="replace")

            ship1 = {"log": "main-20261006.md", "decisions": ["ship 1"]}
            self.assertEqual(run(ship1).returncode, 0)
            retry = run(ship1)
            self.assertEqual(retry.returncode, 0, retry.stderr)
            self.assertIn("already-recorded", retry.stdout)
            second = run({"log": "main-20261006.md", "decisions": ["ship 2"]})
            self.assertEqual(second.returncode, 1)
            self.assertIn("main--2-20261006.md", second.stderr)
            self.assertEqual(len(list(ace.iter_entries(path))), 1)


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

    # --- C2 hardening (spec audit-chain-tamper-evidence AC-1/2/3, Work Log D-2) ---

    def test_migrate_fills_only_missing_then_idempotent(self) -> None:
        """AC-1: migrate adds prev_sha only to entries lacking it; re-run = no-op."""
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            path.write_text(
                json.dumps({"i": 1}, sort_keys=True) + "\n"
                + json.dumps({"i": 2}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(ace.migrate(path), 2)
            self.assertEqual(ace.migrate(path), 0)  # idempotent
            intact, _ = cac.check_chain(path)
            self.assertTrue(intact)

    def test_migrate_refuses_to_rebless_tampered_entry(self) -> None:
        """AC-2: an existing-but-mismatched prev_sha (tampering) → no write, exit-level error.

        This is the C2 anti-laundering guarantee: editing a middle entry then
        running migrate MUST NOT silently recompute the chain over forged content.
        """
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            ace.append_chained(path, {"i": 1, "decision": "real"})
            ace.append_chained(path, {"i": 2, "decision": "real"})
            ace.append_chained(path, {"i": 3, "decision": "real"})
            # Attacker edits the middle entry's content (breaks entry-3's prev_sha link)
            lines = path.read_text(encoding="utf-8").splitlines()
            obj1 = json.loads(lines[1])
            obj1["decision"] = "FORGED"
            lines[1] = json.dumps(obj1, sort_keys=True, ensure_ascii=False)
            tampered = "\n".join(lines) + "\n"
            path.write_text(tampered, encoding="utf-8")
            # migrate MUST refuse (raise) and leave the file byte-for-byte unchanged
            with self.assertRaises(ValueError):
                ace.migrate(path)
            self.assertEqual(path.read_text(encoding="utf-8"), tampered)
            # And the chain remains BROKEN (forgery not laundered)
            intact, _ = cac.check_chain(path)
            self.assertFalse(intact)

    def test_migrate_mixed_missing_and_tampered_no_partial_write(self) -> None:
        """AC-3: missing prev_sha on some entries + a tampered prev_sha later → refuse, no partial write."""
        with tempfile.TemporaryDirectory() as base_dir:
            path = Path(base_dir) / "log.jsonl"
            # entry 0: missing prev_sha; entry 1: present but WRONG (tampered)
            content = (
                json.dumps({"i": 1}, sort_keys=True) + "\n"
                + json.dumps({"i": 2, "prev_sha": "deadbeef"}, sort_keys=True) + "\n"
            )
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(ValueError):
                ace.migrate(path)
            self.assertEqual(path.read_text(encoding="utf-8"), content)  # no partial write


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
