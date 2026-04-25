"""Unit tests for ADR-002 D2.1 — guard_context_write.py extensions.

Spec: docs/specs/lock-unification.md (AC-1..AC-8, AC-22)
Run: python -m unittest discover -s tests/guard -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Make tools/ importable
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))

import guard_context_write as gw  # noqa: E402


def _isolated_repo() -> tempfile.TemporaryDirectory:
    """Create a temp repo with .agent/config.yaml + .agentcortex/context/ scaffolding."""
    tmp = tempfile.TemporaryDirectory()
    base = Path(tmp.name)
    (base / ".agent").mkdir()
    (base / ".agent" / "config.yaml").write_text(
        "guard_policy:\n"
        "  protected_paths:\n"
        '    - ".agentcortex/context/**"\n'
        '    - "AGENTS.md"\n'
        '    - "docs/specs/_product-backlog.md"\n'
        "  allow_outside_paths: false\n"
        "  lock_stale_seconds: 30\n"
        '  receipt_dir: ".agentcortex/context/.guard_receipts"\n'
        "  per_target_receipts: true\n"
        "  legacy_receipt_mirror: true\n",
        encoding="utf-8",
    )
    (base / ".agentcortex" / "context").mkdir(parents=True)
    return tmp


class TestPolicyLoad(unittest.TestCase):
    """AC-1: config.yaml guard_policy block loads with defaults applied."""

    def test_loads_from_config(self) -> None:
        with _isolated_repo() as base_dir:
            base = Path(base_dir)
            policy = gw.load_guard_policy(base)
            self.assertEqual(len(policy["protected_paths"]), 3)
            self.assertEqual(policy["lock_stale_seconds"], 30)
            self.assertTrue(policy["per_target_receipts"])
            self.assertTrue(policy["legacy_receipt_mirror"])

    def test_missing_config_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir)
            policy = gw.load_guard_policy(base)
            # Falls back to DEFAULT_PROTECTED_PATHS (9 entries)
            self.assertEqual(len(policy["protected_paths"]), 9)


class TestPathMatching(unittest.TestCase):
    """AC-2: protected_paths glob matching."""

    def setUp(self) -> None:
        self.globs = [
            ".agentcortex/context/**",
            "AGENTS.md",
            ".agent/workflows/**",
            "docs/architecture/*.log.md",
            "docs/specs/_product-backlog.md",
        ]

    def test_exact_file(self) -> None:
        self.assertTrue(gw.match_protected_path("AGENTS.md", self.globs))

    def test_recursive_glob(self) -> None:
        self.assertTrue(gw.match_protected_path(".agentcortex/context/work/foo.md", self.globs))
        self.assertTrue(gw.match_protected_path(".agent/workflows/bootstrap.md", self.globs))

    def test_single_segment_glob(self) -> None:
        self.assertTrue(gw.match_protected_path("docs/architecture/foo.log.md", self.globs))
        # Negative: matches glob shape but for non-log file:
        self.assertFalse(gw.match_protected_path("docs/architecture/foo.md", self.globs))

    def test_unmatched(self) -> None:
        self.assertFalse(gw.match_protected_path("random.txt", self.globs))
        self.assertFalse(gw.match_protected_path("src/main.py", self.globs))


class TestResolveTargetPolicy(unittest.TestCase):
    """AC-2: resolve_target enforces policy in policy mode; legacy mode preserved."""

    def test_policy_accepts_protected(self) -> None:
        with _isolated_repo() as base_dir:
            base = Path(base_dir)
            policy = gw.load_guard_policy(base)
            agents = base / "AGENTS.md"
            agents.write_text("# placeholder\n")
            resolved = gw.resolve_target(base, "AGENTS.md", policy=policy, allow_outside=False)
            self.assertEqual(resolved, agents.resolve())

    def test_policy_rejects_unprotected(self) -> None:
        with _isolated_repo() as base_dir:
            base = Path(base_dir)
            policy = gw.load_guard_policy(base)
            with self.assertRaises(ValueError) as ctx:
                gw.resolve_target(base, "random.txt", policy=policy, allow_outside=False)
            self.assertIn("matches no guard_policy", str(ctx.exception))

    def test_legacy_mode_preserved(self) -> None:
        # AC-21: legacy mode (policy=None) keeps the .agentcortex/context/ restriction
        with _isolated_repo() as base_dir:
            base = Path(base_dir)
            (base / ".agentcortex" / "context" / "work").mkdir()
            ok = gw.resolve_target(base, ".agentcortex/context/work/foo.md", policy=None)
            self.assertTrue(str(ok).endswith("foo.md"))
            with self.assertRaises(ValueError):
                gw.resolve_target(base, "AGENTS.md", policy=None)


class TestPidAlive(unittest.TestCase):
    """AC-6: liveness check works on POSIX (and Windows via ctypes)."""

    def test_self_alive(self) -> None:
        self.assertTrue(gw.pid_alive(os.getpid()))

    def test_invalid_pid(self) -> None:
        self.assertFalse(gw.pid_alive(99_999_999))

    def test_zero_or_negative(self) -> None:
        self.assertFalse(gw.pid_alive(0))
        self.assertFalse(gw.pid_alive(-1))


class TestStaleLockThreshold(unittest.TestCase):
    """AC-7: env var overrides policy overrides hardcoded default."""

    def test_default_is_900(self) -> None:
        os.environ.pop("ACX_GUARD_STALE_SECONDS", None)
        self.assertEqual(gw.stale_lock_threshold(), gw.LOCK_STALE_SECONDS)

    def test_policy_value(self) -> None:
        os.environ.pop("ACX_GUARD_STALE_SECONDS", None)
        self.assertEqual(gw.stale_lock_threshold({"lock_stale_seconds": 60}), 60)

    def test_env_overrides_policy(self) -> None:
        os.environ["ACX_GUARD_STALE_SECONDS"] = "42"
        try:
            self.assertEqual(gw.stale_lock_threshold({"lock_stale_seconds": 60}), 42)
        finally:
            os.environ.pop("ACX_GUARD_STALE_SECONDS", None)


class TestClearStaleLockLiveness(unittest.TestCase):
    """AC-6: live PID overrides age — never clear a lock held by a running process."""

    def test_live_pid_blocks_clear(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir)
            lock = base / "x.lock"
            # Backdate timestamp far past stale threshold
            lock.write_text(json.dumps({"pid": os.getpid(), "timestamp": 1}))
            cleared = gw.clear_stale_lock(lock, policy={"lock_stale_seconds": 1})
            self.assertFalse(cleared, "should not clear live-pid lock regardless of age")
            self.assertTrue(lock.exists())

    def test_dead_pid_clears(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir)
            lock = base / "x.lock"
            lock.write_text(json.dumps({"pid": 99_999_999, "timestamp": 1}))
            cleared = gw.clear_stale_lock(lock, policy={"lock_stale_seconds": 1})
            self.assertTrue(cleared)
            self.assertFalse(lock.exists())

    def test_no_pid_respects_age(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir)
            lock = base / "x.lock"
            # No pid field, recent timestamp -> should NOT clear
            lock.write_text(json.dumps({"timestamp": int(time.time())}))
            cleared = gw.clear_stale_lock(lock, policy={"lock_stale_seconds": 3600})
            self.assertFalse(cleared)
            self.assertTrue(lock.exists())


class TestAppendWrite(unittest.TestCase):
    """AC-3, AC-4: append_write uses O_APPEND."""

    def test_single_append(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            target = Path(base_dir) / "log.jsonl"
            gw.append_write(target, '{"a": 1}\n')
            gw.append_write(target, '{"a": 2}\n')
            content = target.read_text(encoding="utf-8")
            lines = [ln for ln in content.split("\n") if ln]
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0]), {"a": 1})
            self.assertEqual(json.loads(lines[1]), {"a": 2})


class TestPerTargetReceipt(unittest.TestCase):
    """AC-5: per-target receipt path is deterministic via sha256."""

    def test_path_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir).resolve()
            target = base / "AGENTS.md"
            p1 = gw.per_target_receipt_path(base, target, ".agentcortex/context/.guard_receipts")
            p2 = gw.per_target_receipt_path(base, target, ".agentcortex/context/.guard_receipts")
            self.assertEqual(p1, p2)
            self.assertTrue(p1.name.endswith(".json"))
            # 16-hex-char digest stem
            self.assertEqual(len(p1.stem), 16)


class TestWriteReceiptDualMirror(unittest.TestCase):
    """AC-22: Phase 1 dual-write produces BOTH per-target AND legacy receipts."""

    def test_dual_write(self) -> None:
        with _isolated_repo() as base_dir:
            base = Path(base_dir).resolve()
            (base / ".agentcortex" / "context" / "work").mkdir()
            target = base / ".agentcortex" / "context" / "work" / "demo.md"
            target.write_text("hi", encoding="utf-8")
            policy = gw.load_guard_policy(base)
            receipt = gw.write_receipt(
                base,
                ".agentcortex/context/.guard_receipt.json",
                target=target,
                expected_sha="sha-old",
                new_sha="sha-new",
                mode="replace",
                policy=policy,
            )
            self.assertTrue(receipt.exists(), "per-target receipt missing")
            self.assertTrue(
                (base / ".agentcortex" / "context" / ".guard_receipt.json").exists(),
                "legacy receipt missing (dual-write broken)",
            )


class TestLockGroup(unittest.TestCase):
    """AC-8: lock_group([single]) works; lock_group([multi]) raises NotImplementedError."""

    def test_single_path(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir)
            target = base / ".agentcortex" / "context" / "work" / "foo.md"
            target.parent.mkdir(parents=True)
            target.write_text("hi")
            with gw.lock_group([target], root=base):
                pass  # acquire + release

    def test_multi_path_not_implemented(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir)
            with self.assertRaises(NotImplementedError):
                with gw.lock_group(["a", "b"], root=base):
                    pass

    def test_empty_no_op(self) -> None:
        with gw.lock_group([], root=Path(".")):
            pass  # zero-path call is a no-op (does not raise)


if __name__ == "__main__":
    unittest.main()
