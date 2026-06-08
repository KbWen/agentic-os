"""Tests for advisory Work Log lock auto-recovery.

Spec: docs/specs/worklog-lock-auto-recovery.md (AC-1..AC-6)
Run: python -m unittest tests.guard.test_worklog_lock_recovery -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / ".agentcortex" / "tools"
sys.path.insert(0, str(TOOLS))

import recover_worklog_lock as wl  # noqa: E402


NOW = datetime(2026, 6, 8, 12, 15, tzinfo=timezone.utc)


def _lock_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "owner": "other",
        "session": "other-session",
        "branch": "codex/issue-188-lock-auto-recovery",
        "phase": "bootstrap",
        "updated_at": NOW.isoformat(),
        "stale_timeout_minutes": 60,
    }
    payload.update(overrides)
    return payload


def _worklog(path: Path) -> None:
    path.write_text(
        "# Work Log: demo\n\n"
        "## Drift Log\n\n"
        "none\n\n"
        "---\n\n"
        "## Evidence\n\n"
        "none\n",
        encoding="utf-8",
    )


class TestWorklogLockRecovery(unittest.TestCase):
    def test_missing_lock_created(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            lock = Path(base_dir) / "demo.lock.json"
            result = wl.ensure_lock(
                lock,
                owner="codex",
                session="codex-session",
                branch="codex/issue-188-lock-auto-recovery",
                phase="bootstrap",
                now=NOW,
            )

            self.assertEqual(result.status, "created")
            data = json.loads(lock.read_text(encoding="utf-8"))
            self.assertEqual(data["owner"], "codex")
            self.assertEqual(data["session"], "codex-session")
            self.assertEqual(data["branch"], "codex/issue-188-lock-auto-recovery")
            self.assertEqual(data["phase"], "bootstrap")
            self.assertEqual(data["updated_at"], NOW.isoformat())
            self.assertEqual(data["stale_timeout_minutes"], 60)

    def test_stale_time_recovered_and_drift_logged(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir)
            lock = base / "demo.lock.json"
            worklog = base / "demo.md"
            _worklog(worklog)
            lock.write_text(
                json.dumps(
                    _lock_payload(
                        updated_at=datetime(2026, 6, 8, 10, 0, tzinfo=timezone.utc).isoformat(),
                        stale_timeout_minutes=30,
                    )
                ),
                encoding="utf-8",
            )

            result = wl.ensure_lock(
                lock,
                owner="codex",
                session="codex-session",
                branch="codex/issue-188-lock-auto-recovery",
                phase="implement",
                worklog=worklog,
                now=NOW,
            )

            self.assertEqual(result.status, "recovered")
            self.assertEqual(result.reason, "stale-time")
            data = json.loads(lock.read_text(encoding="utf-8"))
            self.assertEqual(data["owner"], "codex")
            content = worklog.read_text(encoding="utf-8")
            self.assertIn("Recovered stale Work Log lock", content)
            self.assertIn("prior_owner=other", content)
            self.assertNotIn("\nnone\n", content.split("## Drift Log", 1)[1].split("---", 1)[0])

    def test_dead_pid_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            lock = Path(base_dir) / "demo.lock.json"
            lock.write_text(json.dumps(_lock_payload(pid=99_999_999)), encoding="utf-8")

            result = wl.ensure_lock(
                lock,
                owner="codex",
                session="codex-session",
                branch="codex/issue-188-lock-auto-recovery",
                phase="bootstrap",
                now=NOW,
            )

            self.assertEqual(result.status, "recovered")
            self.assertEqual(result.reason, "dead-pid")
            self.assertEqual(json.loads(lock.read_text(encoding="utf-8"))["owner"], "codex")

    def test_corrupted_lock_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir)
            lock = base / "demo.lock.json"
            worklog = base / "demo.md"
            _worklog(worklog)
            lock.write_text("{not-json", encoding="utf-8")

            result = wl.ensure_lock(
                lock,
                owner="codex",
                session="codex-session",
                branch="codex/issue-188-lock-auto-recovery",
                phase="bootstrap",
                worklog=worklog,
                now=NOW,
            )

            self.assertEqual(result.status, "recovered")
            self.assertEqual(result.reason, "invalid-json")
            self.assertEqual(json.loads(lock.read_text(encoding="utf-8"))["owner"], "codex")
            self.assertIn("reason=invalid-json", worklog.read_text(encoding="utf-8"))

    def test_active_lock_preserved_by_api_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            lock = Path(base_dir) / "demo.lock.json"
            lock.write_text(json.dumps(_lock_payload(pid=os.getpid())), encoding="utf-8")

            result = wl.ensure_lock(
                lock,
                owner="codex",
                session="codex-session",
                branch="codex/issue-188-lock-auto-recovery",
                phase="bootstrap",
                now=NOW,
            )

            self.assertEqual(result.status, "active")
            self.assertEqual(result.exit_code, 2)
            self.assertEqual(json.loads(lock.read_text(encoding="utf-8"))["owner"], "other")

            cli = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "recover_worklog_lock.py"),
                    "ensure",
                    "--lock",
                    str(lock),
                    "--owner",
                    "codex",
                    "--session",
                    "codex-session",
                    "--branch",
                    "codex/issue-188-lock-auto-recovery",
                    "--phase",
                    "bootstrap",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(cli.returncode, 2)
            self.assertIn("active", cli.stdout + cli.stderr)
            self.assertEqual(json.loads(lock.read_text(encoding="utf-8"))["owner"], "other")

    def test_cli_created_lock_is_preserved_until_stale(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            lock = Path(base_dir) / "demo.lock.json"

            first = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "recover_worklog_lock.py"),
                    "ensure",
                    "--lock",
                    str(lock),
                    "--owner",
                    "agent-a",
                    "--session",
                    "session-a",
                    "--branch",
                    "codex/hotfix-worklog-lock-cli-pid",
                    "--phase",
                    "bootstrap",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0)
            self.assertNotIn("pid", json.loads(lock.read_text(encoding="utf-8")))

            second = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "recover_worklog_lock.py"),
                    "ensure",
                    "--lock",
                    str(lock),
                    "--owner",
                    "agent-b",
                    "--session",
                    "session-b",
                    "--branch",
                    "codex/hotfix-worklog-lock-cli-pid",
                    "--phase",
                    "bootstrap",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(second.returncode, 2)
            self.assertIn("active", second.stdout + second.stderr)
            self.assertEqual(json.loads(lock.read_text(encoding="utf-8"))["owner"], "agent-a")

    def test_cli_explicit_owner_pid_preserves_active_lock(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            lock = Path(base_dir) / "demo.lock.json"

            first = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "recover_worklog_lock.py"),
                    "ensure",
                    "--lock",
                    str(lock),
                    "--owner",
                    "agent-a",
                    "--session",
                    "session-a",
                    "--branch",
                    "codex/hotfix-worklog-lock-cli-pid",
                    "--phase",
                    "bootstrap",
                    "--pid",
                    str(os.getpid()),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0)
            self.assertEqual(json.loads(lock.read_text(encoding="utf-8"))["pid"], os.getpid())

            second = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "recover_worklog_lock.py"),
                    "ensure",
                    "--lock",
                    str(lock),
                    "--owner",
                    "agent-b",
                    "--session",
                    "session-b",
                    "--branch",
                    "codex/hotfix-worklog-lock-cli-pid",
                    "--phase",
                    "bootstrap",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(second.returncode, 2)
            self.assertEqual(json.loads(lock.read_text(encoding="utf-8"))["owner"], "agent-a")

    def test_bootstrap_documents_recovery_helper(self) -> None:
        bootstrap = (ROOT / ".agent" / "workflows" / "bootstrap.md").read_text(encoding="utf-8")
        self.assertIn(".agentcortex/tools/recover_worklog_lock.py ensure", bootstrap)
        self.assertIn("Drift Log", bootstrap)


if __name__ == "__main__":
    unittest.main()
