from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import pytest
from pathlib import Path

from test_helpers import sanitize_deployed_ssot

ROOT = Path(__file__).resolve().parents[2]


def run_process(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)


# The utilities the shipped shell scripts need at startup (deploy.sh calls
# `dirname` on line 4 and `mktemp` on line 549). Mirrors the acceptance probe in
# .agentcortex/bin/deploy.ps1 — see has_bash_launcher for why --version is not
# a sufficient test.
BASH_LAUNCHER_PROBE = "command -v dirname >/dev/null 2>&1 && command -v mktemp >/dev/null 2>&1"


def has_bash_launcher(candidates: list[str] | None = None) -> bool:
    """True when a bash that can actually run the shipped shell scripts exists.

    Two candidate classes answer `bash --version` with exit 0 yet cannot run
    deploy.sh: a WindowsApps `bash.exe` (a WSL placeholder when no distro is
    installed) and a bare `<git>/usr/bin/bash.exe` (no /usr/bin on PATH, so
    `dirname` and `mktemp` do not resolve). A broken app-execution alias can also
    fail at process start, raising OSError. This function is evaluated at import
    time by `skipUnless` decorators here and in test_backlog_validation.py, so an
    uncaught raise aborts collection for both modules instead of skipping one
    candidate.
    """
    if candidates is None:
        candidates = []
        which_bash = shutil.which("bash")
        if which_bash:
            candidates.append(which_bash)
        candidates.extend(
            [
                "C:/Program Files/Git/bin/bash.exe",
                "C:/Program Files/Git/usr/bin/bash.exe",
                "C:/Program Files (x86)/Git/bin/bash.exe",
            ]
        )
    for candidate in candidates:
        if not candidate or "WindowsApps" in candidate:
            continue
        if not Path(candidate).is_file():
            continue
        try:
            probe = subprocess.run(
                [candidate, "-c", BASH_LAUNCHER_PROBE],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except OSError:
            continue
        if probe.returncode == 0:
            return True
    return False


def run_deploy(target: Path) -> subprocess.CompletedProcess[str]:
    if os.name == "nt":
        return run_process(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / ".agentcortex/bin/deploy.ps1"), str(target)],
            ROOT,
        )
    return run_process(["bash", str(ROOT / ".agentcortex/bin/deploy.sh"), str(target)], ROOT)


def run_validate(target: Path) -> subprocess.CompletedProcess[str]:
    if os.name == "nt":
        return run_process(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(target / ".agentcortex/bin/validate.ps1")],
            target,
        )
    return run_process(["bash", str(target / ".agentcortex/bin/validate.sh")], target)


def init_git_repo(target: Path) -> None:
    init_git = run_process(["git", "init"], target)
    if init_git.returncode != 0:
        raise AssertionError(init_git.stderr or init_git.stdout)
    add_all = run_process(["git", "add", "-A"], target)
    if add_all.returncode != 0:
        raise AssertionError(add_all.stderr or add_all.stdout)


# Each test spawns a full validate.sh run (~40s each) — fidelity by design.
pytestmark = pytest.mark.slow


@unittest.skipUnless(has_bash_launcher(), "bash launcher unavailable for deploy smoke")
class SSOTCompletenessTests(unittest.TestCase):
    def test_adr_not_indexed_fails(self) -> None:
        """ADR file on disk but not in SSoT ADR Index → validator must fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            (target / "docs/adr").mkdir(parents=True, exist_ok=True)
            (target / "docs/adr/ADR-099-test.md").write_text(
                "# ADR-099 Test\n",
                encoding="utf-8",
            )

            validate = run_validate(target)
            self.assertNotEqual(validate.returncode, 0, validate.stdout)
            self.assertIn("SSoT ADR Index completeness", validate.stdout)
            self.assertIn("FAIL", validate.stdout)
            self.assertIn("not indexed", validate.stdout)

    def test_phantom_adr_fails(self) -> None:
        """ADR entry in SSoT ADR Index but no file on disk → validator must fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            ssot = target / ".agentcortex" / "context" / "current_state.md"
            content = ssot.read_text(encoding="utf-8")
            # Handle both 'none' form and multi-line entry form produced by sanitize
            updated = re.sub(
                r'(\*\*ADR Index\*\*:)\s*none',
                r'\1\n  - docs/adr/ADR-999-phantom.md',
                content,
            )
            if updated == content:
                # ADR index already has entries — append phantom after existing entries
                updated = re.sub(
                    r'(\*\*ADR Index\*\*:[^\n]*\n(?:\s+-\s+\S.*\.md\n)*)',
                    r'\1  - docs/adr/ADR-999-phantom.md\n',
                    content,
                )
            ssot.write_text(updated, encoding="utf-8")

            validate = run_validate(target)
            self.assertNotEqual(validate.returncode, 0, validate.stdout)
            self.assertIn("phantom index entry", validate.stdout)

    def test_spec_not_indexed_fails(self) -> None:
        """Shipped spec on disk but not in SSoT Spec Index → validator must fail.

        Per ADR-010, the Spec Index completeness check requires an index entry only
        for shipped/living specs; pre-ship draft/frozen/cancelled states are skipped
        (a legal `status: frozen` spec must NOT fail — covered by
        tests/ci/test_validator_false_positives.py::test_adr010_*). A `status: shipped`
        spec missing from the index is still a real defect and must FAIL.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            (target / "docs/specs").mkdir(parents=True, exist_ok=True)
            (target / "docs/specs/test-feature.md").write_text(
                "---\nstatus: shipped\ntitle: Test Feature\n---\n\n# Test Feature\n",
                encoding="utf-8",
            )

            validate = run_validate(target)
            self.assertNotEqual(validate.returncode, 0, validate.stdout)
            self.assertIn("Spec Index completeness", validate.stdout)
            self.assertIn("not indexed", validate.stdout)

    def test_draft_spec_excluded(self) -> None:
        """Draft spec on disk without Spec Index entry → validator must pass (drafts excluded)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            (target / "docs/specs").mkdir(parents=True, exist_ok=True)
            (target / "docs/specs/draft-proposal.md").write_text(
                "---\nstatus: draft\ntitle: Draft Proposal\n---\n\n# Draft Proposal\n",
                encoding="utf-8",
            )

            validate = run_validate(target)
            self.assertEqual(validate.returncode, 0, validate.stderr or validate.stdout)

    def test_spec_folded_into_archive_section_passes(self) -> None:
        """Shipped spec whose index line was collapsed into `## Spec Index Archive` → PASS.

        This is the `/ship` Spec Index Cap remedy (ship.md §State Update & Archival).
        Before #143 the completeness check read only the live index block, so following
        the documented remedy produced `N shipped/living spec(s) not in index` — a hard
        FAIL. The remedy had never been executed, so the defect went unnoticed. The spec
        body deliberately stays in `docs/specs/`; only the index line moves.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            (target / "docs/specs").mkdir(parents=True, exist_ok=True)
            (target / "docs/specs/folded-feature.md").write_text(
                "---\nstatus: shipped\ntitle: Folded Feature\n---\n\n# Folded Feature\n",
                encoding="utf-8",
            )

            ssot = target / ".agentcortex" / "context" / "current_state.md"
            ssot.write_text(
                ssot.read_text(encoding="utf-8")
                + "\n## Spec Index Archive\n\n"
                + "  - docs/specs/folded-feature.md — Folded Feature, [Shipped 2026-01-01]\n",
                encoding="utf-8",
            )

            validate = run_validate(target)
            self.assertEqual(validate.returncode, 0, validate.stdout)
            self.assertNotIn("not indexed", validate.stdout)

    def test_spec_path_in_prose_after_heading_does_not_count_as_indexed(self) -> None:
        """A spec path in prose below a `##` heading must NOT satisfy the index (#143).

        `validate.sh`'s live-index awk used to stop only at the next `- **` bullet,
        so it read straight through an intervening `## ` heading and any spec path
        mentioned in prose there counted as "indexed" — a false PASS. `validate.ps1`
        already stopped at `\\n##`, so the two platforms disagreed: PASS on Linux,
        FAIL on Windows. Both now stop at `^##`. This pins the stricter, converged
        behavior so the loose bash form cannot come back.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            (target / "docs/specs").mkdir(parents=True, exist_ok=True)
            (target / "docs/specs/prose-only.md").write_text(
                "---\nstatus: shipped\ntitle: Prose Only\n---\n\n# Prose Only\n",
                encoding="utf-8",
            )

            # Insert a `##` section between the Spec Index block and the next
            # top-level bullet, mentioning the spec path in prose only.
            ssot = target / ".agentcortex" / "context" / "current_state.md"
            content = ssot.read_text(encoding="utf-8")
            marker = "- **Canonical Commands**"
            self.assertIn(marker, content, "fixture precondition: template shape changed")
            ssot.write_text(
                content.replace(
                    marker,
                    "## Ship Notes\n\n- shipped docs/specs/prose-only.md earlier\n\n" + marker,
                    1,
                ),
                encoding="utf-8",
            )

            validate = run_validate(target)
            self.assertNotEqual(validate.returncode, 0, validate.stdout)
            self.assertIn("docs/specs/prose-only.md", validate.stdout)
            self.assertIn("not indexed", validate.stdout)

    def test_phantom_spec_in_archive_section_fails(self) -> None:
        """Archived index line whose spec file is gone → still a phantom → FAIL.

        The archive section is in scope for the reverse check too, so collapsing an
        entry must not become a way to hide a dangling reference (#143).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            ssot = target / ".agentcortex" / "context" / "current_state.md"
            ssot.write_text(
                ssot.read_text(encoding="utf-8")
                + "\n## Spec Index Archive\n\n"
                + "  - docs/specs/never-existed.md — Ghost, [Shipped 2026-01-01]\n",
                encoding="utf-8",
            )

            validate = run_validate(target)
            self.assertNotEqual(validate.returncode, 0, validate.stdout)
            # Assert the spec path, not just "phantom index entry" — the ADR branch
            # (validate.sh:2349 / validate.ps1:2220) emits the identical string.
            self.assertIn("docs/specs/never-existed.md", validate.stdout)

    def test_backlog_exists_but_ssot_says_none_fails(self) -> None:
        """Backlog file exists on disk but SSoT Active Backlog is 'none' → validator must fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            (target / "docs/specs").mkdir(parents=True, exist_ok=True)
            (target / "docs/specs/_product-backlog.md").write_text(
                "# Product Backlog\n",
                encoding="utf-8",
            )

            validate = run_validate(target)
            self.assertNotEqual(validate.returncode, 0, validate.stdout)
            self.assertIn("Active Backlog consistency", validate.stdout)

    def test_phantom_backlog_ref_fails(self) -> None:
        """SSoT Active Backlog references a file that does not exist on disk → validator must fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            ssot = target / ".agentcortex" / "context" / "current_state.md"
            content = ssot.read_text(encoding="utf-8")
            content = re.sub(
                r'(\*\*Active Backlog\*\*:)\s*none',
                r'\1 `docs/specs/_product-backlog.md`',
                content,
            )
            ssot.write_text(content, encoding="utf-8")

            validate = run_validate(target)
            self.assertNotEqual(validate.returncode, 0, validate.stdout)
            self.assertIn("does not exist", validate.stdout)

    def test_backlog_path_value_mismatch_fails(self) -> None:
        """Backlog file exists but SSoT Active Backlog references a different path → validator must fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            # Create the actual backlog file at the canonical path
            (target / "docs/specs").mkdir(parents=True, exist_ok=True)
            (target / "docs/specs/_product-backlog.md").write_text(
                "# Product Backlog\n",
                encoding="utf-8",
            )
            # Also create the wrong-path file so the phantom check doesn't fire
            (target / "docs/specs/wrong-backlog.md").write_text(
                "# Wrong Backlog\n",
                encoding="utf-8",
            )

            # Point SSoT to the wrong path
            ssot = target / ".agentcortex" / "context" / "current_state.md"
            content = ssot.read_text(encoding="utf-8")
            content = re.sub(
                r'(\*\*Active Backlog\*\*:)\s*none',
                r'\1 `docs/specs/wrong-backlog.md`',
                content,
            )
            ssot.write_text(content, encoding="utf-8")

            validate = run_validate(target)
            self.assertNotEqual(validate.returncode, 0, validate.stdout)
            self.assertIn("actual backlog", validate.stdout)

    def test_clean_state_passes(self) -> None:
        """Clean deploy with sanitized SSoT → validator must pass (baseline)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            validate = run_validate(target)
            self.assertEqual(validate.returncode, 0, validate.stderr or validate.stdout)


class BashLauncherProbeTests(unittest.TestCase):
    """has_bash_launcher is evaluated at import time by skipUnless decorators in
    this module and in test_backlog_validation.py. A candidate that cannot be
    started, or that starts but cannot run the shipped scripts, must be skipped
    — never propagated as a collection error, never accepted."""

    @staticmethod
    def _touch(directory: str, name: str) -> str:
        path = Path(directory) / name
        path.write_bytes(b"")
        return str(path)

    def test_process_start_failure_falls_through_to_next_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            broken = self._touch(tmpdir, "broken-alias.exe")
            usable = self._touch(tmpdir, "real-bash.exe")
            probed: list[str] = []

            def fake_run(args, **kwargs):  # noqa: ANN001, ANN003 - test double
                probed.append(args[0])
                if args[0] == broken:
                    # The WindowsApps alias signature: OSError at process start.
                    raise OSError(1312, "A specified logon session does not exist")
                return subprocess.CompletedProcess(args, 0, "", "")

            with mock.patch.object(subprocess, "run", side_effect=fake_run):
                self.assertTrue(has_bash_launcher([broken, usable]))
            self.assertEqual(probed, [broken, usable], "search must continue past the raising candidate")

    def test_windowsapps_alias_is_never_started(self) -> None:
        alias = "C:/Users/x/AppData/Local/Microsoft/WindowsApps/bash.exe"
        with mock.patch.object(subprocess, "run") as runner:
            self.assertFalse(has_bash_launcher([alias]))
        runner.assert_not_called()

    def test_launcher_without_coreutils_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bare = self._touch(tmpdir, "bare-bash.exe")
            probes: list[list[str]] = []

            def fake_run(args, **kwargs):  # noqa: ANN001, ANN003 - test double
                probes.append(list(args))
                # A bare <git>/usr/bin/bash.exe: bash runs, coreutils do not.
                return subprocess.CompletedProcess(args, 127, "", "dirname: command not found")

            with mock.patch.object(subprocess, "run", side_effect=fake_run):
                self.assertFalse(has_bash_launcher([bare]))
            self.assertEqual(probes, [[bare, "-c", BASH_LAUNCHER_PROBE]])

    def test_all_candidates_failing_returns_false(self) -> None:
        self.assertFalse(has_bash_launcher([]))
        self.assertFalse(has_bash_launcher(["", "C:/nonexistent/bash.exe"]))


if __name__ == "__main__":
    unittest.main()
