"""Regression tests for chain-aware Global Lessons archival (backlog #117).

Covers the four contract scenarios:
  1. archive oldest LOW  -> lesson chain verifies GREEN
  2. removal WITHOUT an archival record -> chain FAILS (fail-closed)
  3. archived entry edited in the archive file -> detectable
  4. cap reached -> append after archival succeeds (cap relief)

Also verifies the audit INDEX itself stays chain-intact after an archival
record is written (the record is appended via the hash-chained helper).

Fixtures are synthetic minimal current_state.md files — the live SSoT is
never touched.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
APPEND_LESSON = TOOLS / "append_lesson.py"
CHECK_LESSON_CHAIN = TOOLS / "check_lesson_chain.py"
CHECK_AUDIT_CHAIN = TOOLS / "check_audit_chain.py"

sys.path.insert(0, str(TOOLS))
from check_lesson_chain import chain_sha  # noqa: E402


def _bullet(cat: str, sev: str, trig: str, prev: str, body: str) -> str:
    return f"- [Category: {cat}][Severity: {sev}][Trigger: {trig}][prev: {prev}] {body}"


def build_current_state(entries: list[tuple[str, str, str, str]]) -> str:
    """entries = list of (cat, sev, trig, body). Prev hashes are auto-chained."""
    lines = [
        "# Project Current State (vNext)",
        "",
        "- **Project Intent**: test fixture.",
        "",
        "## Global Lessons (AI Error Pattern Registry)",
        "",
    ]
    prev = "GENESIS"
    for cat, sev, trig, body in entries:
        lines.append(_bullet(cat, sev, trig, prev, body))
        prev = chain_sha(cat, sev, trig, body)
    lines += ["", "## Ship History", "", "### Ship-fixture", "- Feature shipped: none", ""]
    return "\n".join(lines) + "\n"


def run(tool: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(tool), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )


class LessonChainArchivalTests(unittest.TestCase):
    def _fixture(self, tmp: Path, entries: list[tuple[str, str, str, str]]) -> tuple[Path, Path, Path]:
        ctx = tmp / ".agentcortex" / "context"
        arc = ctx / "archive"
        arc.mkdir(parents=True, exist_ok=True)
        cs = ctx / "current_state.md"
        cs.write_text(build_current_state(entries), encoding="utf-8")
        idx = arc / "INDEX.jsonl"
        arc_md = arc / "global-lessons-archive.md"
        return cs, idx, arc_md

    def _check(self, cs: Path, idx: Path) -> subprocess.CompletedProcess[str]:
        return run(CHECK_LESSON_CHAIN, "--path", str(cs), "--index-jsonl", str(idx))

    def _entries(self) -> list[tuple[str, str, str, str]]:
        return [
            ("cat-a", "MEDIUM", "trig-a", "First entry (genesis-anchored)."),
            ("cat-b", "LOW", "trig-b", "Second entry, oldest LOW — archival candidate."),
            ("cat-c", "LOW", "trig-c", "Third entry, successor to be re-anchored."),
            ("cat-d", "HIGH", "trig-d", "Fourth entry, pinned HIGH."),
        ]

    # ---- Scenario 1: archive oldest LOW -> chain verifies GREEN ----
    def test_archive_oldest_low_chain_stays_green(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cs, idx, arc_md = self._fixture(tmp, self._entries())
            self.assertEqual(self._check(cs, idx).returncode, 0, "baseline chain should be intact")

            # Oldest LOW is index 2.
            res = run(
                APPEND_LESSON, "--archive", "--index", "2",
                "--path", str(cs), "--archive-path", str(arc_md),
                "--index-jsonl", str(idx), "--date", "2026-07-06",
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            payload = json.loads(res.stdout)
            self.assertEqual(payload["op"], "archive")
            self.assertTrue(payload["successor_reanchored"])

            # Chain must still verify GREEN.
            chk = self._check(cs, idx)
            self.assertEqual(chk.returncode, 0, chk.stdout + chk.stderr)
            # Count dropped by one.
            self.assertEqual(cs.read_text(encoding="utf-8").count("- [Category:"), 3)
            # Archive file received the moved bullet.
            self.assertIn("trig-b", arc_md.read_text(encoding="utf-8"))
            # INDEX audit chain stays intact.
            audit = run(CHECK_AUDIT_CHAIN, "--path", str(idx))
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)

    # ---- Scenario 2: removal WITHOUT record -> FAIL (fail-closed) ----
    def test_naive_removal_without_record_fails(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cs, idx, _arc_md = self._fixture(tmp, self._entries())
            # Delete entry #2 raw (no re-anchor, no record).
            lines = cs.read_text(encoding="utf-8").splitlines()
            out, seen = [], 0
            in_sec = False
            for ln in lines:
                if ln.startswith("## Global Lessons"):
                    in_sec = True
                elif in_sec and ln.startswith("## "):
                    in_sec = False
                if in_sec and ln.lstrip().startswith("- [Category:"):
                    seen += 1
                    if seen == 2:
                        continue
                out.append(ln)
            cs.write_text("\n".join(out) + "\n", encoding="utf-8")

            chk = self._check(cs, idx)
            self.assertEqual(chk.returncode, 1, "raw removal must break the chain")
            self.assertIn("chain broken", chk.stdout + chk.stderr)

    # ---- Scenario 3: archived entry edited in the archive -> detectable ----
    def test_archived_entry_edit_is_detected(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cs, idx, arc_md = self._fixture(tmp, self._entries())
            run(
                APPEND_LESSON, "--archive", "--index", "2",
                "--path", str(cs), "--archive-path", str(arc_md),
                "--index-jsonl", str(idx), "--date", "2026-07-06",
            )
            self.assertEqual(self._check(cs, idx).returncode, 0)

            # Edit the archived bullet's body in the archive file.
            txt = arc_md.read_text(encoding="utf-8")
            edited = txt.replace("archival candidate.", "TAMPERED body.")
            self.assertNotEqual(txt, edited, "edit precondition failed")
            arc_md.write_text(edited, encoding="utf-8")

            chk = self._check(cs, idx)
            self.assertEqual(chk.returncode, 1, "archive edit must be detected")
            self.assertIn("archive integrity", chk.stdout + chk.stderr)

    # ---- Scenario 4: cap reached -> append after archival succeeds ----
    def test_append_after_archival_relieves_cap(self):
        import tempfile

        # 20 entries: 1 HIGH head + 19 LOW so index 2 is a valid LOW to archive.
        entries = [("cat-head", "MEDIUM", "trig-head", "Head entry.")]
        for i in range(19):
            entries.append((f"cat-{i}", "LOW", f"trig-{i}", f"Body {i}."))
        self.assertEqual(len(entries), 20)

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cs, idx, arc_md = self._fixture(tmp, entries)

            # At cap: a fresh append must be refused.
            refused = run(
                APPEND_LESSON, "--path", str(cs),
                "--category", "cat-new", "--severity", "LOW",
                "--trigger", "trig-new", "--body", "Should be refused at cap.",
            )
            self.assertEqual(refused.returncode, 1, "append at cap must be refused")
            self.assertIn("cap", refused.stderr.lower())

            # Archive index 2 (a LOW) to free a slot.
            arch = run(
                APPEND_LESSON, "--archive", "--index", "2",
                "--path", str(cs), "--archive-path", str(arc_md),
                "--index-jsonl", str(idx), "--date", "2026-07-06",
            )
            self.assertEqual(arch.returncode, 0, arch.stderr)

            # Now append succeeds and the chain stays intact.
            ok = run(
                APPEND_LESSON, "--path", str(cs),
                "--category", "cat-new", "--severity", "LOW",
                "--trigger", "trig-new", "--body", "Succeeds after archival freed a slot.",
            )
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(self._check(cs, idx).returncode, 0)
            self.assertEqual(cs.read_text(encoding="utf-8").count("- [Category:"), 20)

    # ---- HIGH-severity entries are pinned (cannot be archived) ----
    def test_high_severity_archival_refused(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cs, idx, arc_md = self._fixture(tmp, self._entries())
            # Index 4 is HIGH.
            res = run(
                APPEND_LESSON, "--archive", "--index", "4",
                "--path", str(cs), "--archive-path", str(arc_md),
                "--index-jsonl", str(idx),
            )
            self.assertEqual(res.returncode, 1, "HIGH archival must be refused")
            self.assertIn("HIGH", res.stderr)


if __name__ == "__main__":
    unittest.main()
