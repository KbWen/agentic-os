"""Guard tests for the unresolved merge-conflict-marker validator check.

On 2026-05-31 ``current_state.md`` reached ``main`` carrying committed git
conflict markers from a #121/#122 squash-merge collision (fixed in PR #130).
git's own merge blocks this, but a GitHub squash-merge does not, and neither
validator nor CI caught it. ``validate.sh`` / ``validate.ps1`` gained a check
that FAILs when any tracked file contains unresolved conflict markers.

These tests assert (1) both validators wire in the check with matching strings
(cross-platform parity), and (2) the git-grep detection logic FAILs on a marked
file and PASSes on a clean tree -- including that a markdown setext-H2 underline
(a bare line of ``=``) is NOT flagged, since we match only the unambiguous
opening/closing marker forms.

Marker strings are assembled at runtime so THIS test file contains no column-0
markers of its own (the real validator self-excludes it regardless).
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = REPO_ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = REPO_ROOT / ".agentcortex" / "bin" / "validate.ps1"

# The exact detection pattern both validators use (open/close marker, line-start).
MARKER_PATTERN = r"^(<<<<<<< |>>>>>>> )"

# Built at runtime to avoid embedding column-0 markers in this source file.
OPEN = "<" * 7 + " HEAD"
MID = "=" * 7
CLOSE = ">" * 7 + " branch"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ConflictMarkerStructuralParity(unittest.TestCase):
    """Both validators must wire in the conflict-marker check with parity."""

    def test_sh_has_check(self) -> None:
        body = _read(VALIDATE_SH)
        self.assertIn("merge-conflict markers in tracked files", body)
        self.assertIn(MARKER_PATTERN, body)

    def test_ps1_has_check(self) -> None:
        body = _read(VALIDATE_PS1)
        self.assertIn("merge-conflict markers in tracked files", body)
        self.assertIn(MARKER_PATTERN, body)

    def test_identical_verdict_strings(self) -> None:
        # The PASS/FAIL/WARN messages must be byte-identical across validators
        # so the two platforms produce the same verdict text.
        for phrase in (
            "unresolved merge-conflict markers in tracked files",
            "no unresolved merge-conflict markers in tracked files",
            "merge-conflict marker scan -- git unavailable or not a git repo",
        ):
            self.assertIn(phrase, _read(VALIDATE_SH))
            self.assertIn(phrase, _read(VALIDATE_PS1))

    def test_both_self_exclude_validator_pair(self) -> None:
        # The validator pair must exclude itself (it contains the pattern
        # literally) so the check never self-FAILs.
        for body in (_read(VALIDATE_SH), _read(VALIDATE_PS1)):
            self.assertIn(":(exclude).agentcortex/bin/validate.sh", body)
            self.assertIn(":(exclude).agentcortex/bin/validate.ps1", body)


class ConflictMarkerDetection(unittest.TestCase):
    """The git-grep detection logic FAILs on markers, PASSes on a clean tree."""

    def _git(self, *args: str, cwd: Path) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env.setdefault("GIT_AUTHOR_NAME", "t")
        env.setdefault("GIT_AUTHOR_EMAIL", "t@t")
        env.setdefault("GIT_COMMITTER_NAME", "t")
        env.setdefault("GIT_COMMITTER_EMAIL", "t@t")
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, env=env
        )

    def _grep(self, root: Path) -> subprocess.CompletedProcess:
        # Replicate the exact detection the validators run (sans self-excludes,
        # which the temp repo does not contain).
        return subprocess.run(
            ["git", "grep", "-I", "-n", "-E", MARKER_PATTERN, "--", "."],
            cwd=root, capture_output=True, text=True,
        )

    def _init_repo(self, root: Path) -> None:
        self._git("init", "-q", cwd=root)

    def _commit_all(self, root: Path) -> None:
        self._git("add", "-A", cwd=root)
        self._git("commit", "-q", "-m", "fixture", cwd=root)

    def test_clean_tree_has_no_markers(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._init_repo(root)
            (root / "a.md").write_text("# clean\n\nno markers here\n", encoding="utf-8")
            self._commit_all(root)
            res = self._grep(root)
            self.assertEqual(res.returncode, 1, res.stdout)  # 1 = no matches
            self.assertEqual(res.stdout.strip(), "")

    def test_conflict_markers_detected(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._init_repo(root)
            conflicted = "\n".join(
                ["text before", OPEN, "ours", MID, "theirs", CLOSE, "text after", ""]
            )
            (root / "ssot.md").write_text(conflicted, encoding="utf-8")
            self._commit_all(root)
            res = self._grep(root)
            self.assertEqual(res.returncode, 0, "expected a marker match")  # 0 = matched
            self.assertIn("ssot.md", res.stdout)

    def test_setext_h2_underline_not_flagged(self) -> None:
        # A markdown setext H2 (heading text followed by a line of '=') and a
        # bare 7-equals line must NOT be flagged -- only open/close markers are.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._init_repo(root)
            doc = "\n".join(["Heading", MID, "", "body text", ""])
            (root / "doc.md").write_text(doc, encoding="utf-8")
            self._commit_all(root)
            res = self._grep(root)
            self.assertEqual(res.returncode, 1, res.stdout)  # no open/close → no match


if __name__ == "__main__":
    unittest.main()
