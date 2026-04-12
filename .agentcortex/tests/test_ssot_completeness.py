from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_helpers import sanitize_deployed_ssot

ROOT = Path(__file__).resolve().parents[2]


def run_process(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)


def has_bash_launcher() -> bool:
    candidates: list[str] = []
    if shutil.which("bash"):
        candidates.append(shutil.which("bash") or "")
    candidates.extend(
        [
            "C:/Program Files/Git/bin/bash.exe",
            "C:/Program Files/Git/usr/bin/bash.exe",
            "C:/Program Files (x86)/Git/bin/bash.exe",
        ]
    )
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        probe = subprocess.run(
            [candidate, "--version"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
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
        """Frozen spec on disk but not in SSoT Spec Index → validator must fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            (target / "docs/specs").mkdir(parents=True, exist_ok=True)
            (target / "docs/specs/test-feature.md").write_text(
                "---\nstatus: frozen\ntitle: Test Feature\n---\n\n# Test Feature\n",
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


if __name__ == "__main__":
    unittest.main()
