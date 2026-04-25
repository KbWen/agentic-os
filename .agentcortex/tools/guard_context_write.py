#!/usr/bin/env python3
"""Guarded read/write operations for Agentic OS context files.

ADR-002 (D2.1): policy-driven path scope, append mode, per-target receipts,
configurable lock TTL, process-liveness check, lock_group placeholder.

Spec: docs/specs/lock-unification.md
"""

from __future__ import annotations

import argparse
import errno
import fnmatch
import hashlib
import json
import os
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

# Process-local lock dictionary — serializes threads within ONE Python process
# before they contend for the file-based cross-process lock. Without this,
# pid-based liveness check returns True for a sibling thread, causing deadlock
# under thread-level concurrency (e.g., ThreadPoolExecutor in a single test).
_LOCAL_LOCKS: dict[str, threading.Lock] = {}
_LOCAL_LOCKS_GUARD = threading.Lock()


def _get_local_lock(key: str) -> threading.Lock:
    with _LOCAL_LOCKS_GUARD:
        lock = _LOCAL_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _LOCAL_LOCKS[key] = lock
        return lock


MISSING_SHA = "MISSING"
DEFAULT_RECEIPT = Path(".agentcortex/context/.guard_receipt.json")
LOCK_ROOT = Path(".agentcortex/context/.guard_locks")
CONTEXT_ROOT = Path(".agentcortex/context")
LOCK_STALE_SECONDS = 900
CONFIG_PATH = Path(".agent/config.yaml")

# Default policy used when config.yaml is missing or has no guard_policy block.
# Mirrors the default block written into config.yaml by ADR-002 D2.1 step 1.
DEFAULT_PROTECTED_PATHS: tuple[str, ...] = (
    ".agentcortex/context/**",
    "AGENTS.md",
    ".agent/rules/**",
    ".agent/workflows/**",
    ".agent/config.yaml",
    ".agent/skills/**",
    "docs/adr/**",
    "docs/architecture/*.log.md",
    "docs/specs/_product-backlog.md",
)
DEFAULT_RECEIPT_DIR = Path(".agentcortex/context/.guard_receipts")


# --------------------------------------------------------------------------- #
# Policy loading
# --------------------------------------------------------------------------- #


def _load_yaml(path: Path) -> dict:
    """Parse YAML using the framework's dependency-free loader.

    Falls back to {} on any parse error (capability-by-presence: missing or
    malformed config does not break the guard).
    """
    if not path.is_file():
        return {}
    try:
        # Local import to avoid hard dep when running guard standalone.
        sys.path.insert(0, str(path.parent.resolve().parent / ".agentcortex" / "tools"))
        from _yaml_loader import load_data  # type: ignore
        data = load_data(path)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_guard_policy(root: Path) -> dict:
    """Load .agent/config.yaml §guard_policy with safe defaults."""
    data = _load_yaml(root / CONFIG_PATH)
    policy = data.get("guard_policy", {}) if isinstance(data, dict) else {}
    return {
        "protected_paths": list(policy.get("protected_paths", DEFAULT_PROTECTED_PATHS)),
        "allow_outside_paths": bool(policy.get("allow_outside_paths", False)),
        "lock_stale_seconds": int(policy.get("lock_stale_seconds", LOCK_STALE_SECONDS)),
        "receipt_dir": str(policy.get("receipt_dir", DEFAULT_RECEIPT_DIR.as_posix())),
        "per_target_receipts": bool(policy.get("per_target_receipts", True)),
        "legacy_receipt_mirror": bool(policy.get("legacy_receipt_mirror", True)),
    }


def match_protected_path(rel_posix: str, globs: Sequence[str]) -> bool:
    """Return True if rel_posix matches any glob in the policy list."""
    for pattern in globs:
        if fnmatch.fnmatch(rel_posix, pattern):
            return True
        # fnmatch does not natively handle ** as recursive — emulate by stripping
        # trailing /** and matching prefix.
        if pattern.endswith("/**") and rel_posix.startswith(pattern[:-3] + "/"):
            return True
        if pattern == rel_posix:
            return True
    return False


# --------------------------------------------------------------------------- #
# Process liveness (POSIX + Windows)
# --------------------------------------------------------------------------- #


def pid_alive(pid: int) -> bool:
    """Return True if a process with `pid` is alive on the current host.

    POSIX: signal 0 probes existence without sending a signal.
    Windows: OpenProcess + GetExitCodeProcess via ctypes (stdlib).
    Returns False on permission errors or invalid pid.
    """
    if pid <= 0:
        return False
    if os.name == "nt":  # Windows
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                return False
            try:
                exit_code = ctypes.c_ulong(0)
                if not ctypes.windll.kernel32.GetExitCodeProcess(
                    handle, ctypes.byref(exit_code)
                ):
                    return False
                return exit_code.value == STILL_ACTIVE
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return False
    # POSIX
    try:
        os.kill(pid, 0)
        return True
    except OSError as exc:
        if exc.errno == errno.ESRCH:  # no such process
            return False
        if exc.errno == errno.EPERM:  # process exists but no signal permission
            return True
        return False


# --------------------------------------------------------------------------- #
# Existing helpers (preserved)
# --------------------------------------------------------------------------- #


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely snapshot or write Agentic OS context files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot", help="Read a file and emit its sha256.")
    snapshot.add_argument("--path", required=True, help="Target file path")
    snapshot.add_argument("--root", default=".", help="Repository root")

    write = subparsers.add_parser("write", help="Write a file with optimistic locking.")
    write.add_argument("--path", required=True, help="Target file path")
    write.add_argument("--root", default=".", help="Repository root")
    write.add_argument(
        "--expected-sha",
        default=None,
        help="Expected current sha256 or MISSING (required for replace mode; rejected for append mode)",
    )
    write.add_argument("--lock-key", required=True, help="Stable lock key for the write scope")
    write.add_argument("--input", required=True, help="File that contains the desired new content")
    write.add_argument(
        "--receipt",
        default=str(DEFAULT_RECEIPT),
        help="Legacy receipt path (used when legacy_receipt_mirror is enabled)",
    )
    write.add_argument(
        "--mode",
        choices=("replace", "append"),
        default="replace",
        help="replace: whole-file atomic replace (default); append: O_APPEND single-line atomic append",
    )
    write.add_argument(
        "--allow-outside",
        action="store_true",
        default=False,
        help="Permit writing to paths outside guard_policy.protected_paths (requires policy.allow_outside_paths: true)",
    )
    return parser.parse_args()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_target(root: Path, target: str, *, policy: dict | None = None, allow_outside: bool = False) -> Path:
    """Resolve and validate a write target against the guard policy.

    Backward-compatible: when policy is None, falls back to the legacy
    .agentcortex/context/ restriction (preserves all existing callers).
    """
    path = (root / target).resolve()
    rel_posix = str(path.relative_to(root.resolve())).replace("\\", "/") if path.is_relative_to(root.resolve()) else None

    if policy is None:
        # Legacy mode (pre-ADR-002): only .agentcortex/context/ is writable.
        context_root = (root / CONTEXT_ROOT).resolve()
        try:
            path.relative_to(context_root)
        except ValueError as exc:
            raise ValueError(f"target must stay under {CONTEXT_ROOT.as_posix()}: {target}") from exc
        return path

    # Policy mode (ADR-002 D2.1)
    if rel_posix is None:
        raise ValueError(f"target must stay within repo root: {target}")
    if match_protected_path(rel_posix, policy["protected_paths"]):
        return path
    if allow_outside and policy["allow_outside_paths"]:
        return path
    raise ValueError(
        f"target '{rel_posix}' matches no guard_policy.protected_paths glob; "
        f"pass --allow-outside AND set policy.allow_outside_paths: true to override"
    )


def read_text_and_sha(path: Path) -> tuple[str | None, str]:
    if not path.exists():
        return None, MISSING_SHA
    text = path.read_text(encoding="utf-8")
    return text, sha256_text(text)


def relative_posix(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def lock_path_for_target(root: Path, target: Path) -> Path:
    target_key = relative_posix(target, root)
    digest = hashlib.sha256(target_key.encode("utf-8")).hexdigest()[:16]
    stem = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in target.stem.lower())
    return (root / LOCK_ROOT / f"{stem}-{digest}.lock").resolve()


def lock_age_seconds(lock_path: Path) -> float:
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        timestamp = int(payload.get("timestamp", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        timestamp = int(lock_path.stat().st_mtime)
    return max(0.0, time.time() - timestamp)


def lock_holder_pid(lock_path: Path) -> int | None:
    """Return the PID stored in a lock file, or None if unavailable."""
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        pid = payload.get("pid")
        return int(pid) if pid is not None else None
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def stale_lock_threshold(policy: dict | None = None) -> int:
    """Return the stale-lock TTL in seconds.

    Precedence: ACX_GUARD_STALE_SECONDS env var > policy.lock_stale_seconds > LOCK_STALE_SECONDS
    """
    raw = os.environ.get("ACX_GUARD_STALE_SECONDS", "").strip()
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    if policy is not None:
        return int(policy.get("lock_stale_seconds", LOCK_STALE_SECONDS))
    return LOCK_STALE_SECONDS


def clear_stale_lock(lock_path: Path, *, policy: dict | None = None) -> bool:
    """Clear lock if (a) holder process is dead OR (b) age exceeds threshold.

    Liveness check (ADR-002 D2.1 AC-6): a live PID overrides age — never clear
    a lock held by a running process even if it's been held for a long time.
    """
    try:
        age_seconds = lock_age_seconds(lock_path)
    except FileNotFoundError:
        return True

    pid = lock_holder_pid(lock_path)
    if pid is not None and pid_alive(pid):
        # Live holder — do not clear regardless of age.
        return False

    if pid is None and age_seconds < stale_lock_threshold(policy):
        # Unknown holder; respect age threshold.
        return False

    try:
        lock_path.unlink()
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


@contextmanager
def file_lock(
    lock_path: Path,
    *,
    metadata: dict[str, object] | None = None,
    policy: dict | None = None,
    max_wait_seconds: float = 10.0,
) -> Iterator[None]:
    """Acquire an exclusive file lock with backoff retry under contention.

    Two-stage retry:
      Stage A — stale-clear loop: if lock exists but holder is dead OR aged
                out, clear and retry immediately.
      Stage B — live-holder backoff: if holder is alive, wait with exponential
                backoff (50ms → 1s) until max_wait_seconds elapses.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    local = _get_local_lock(str(lock_path))
    # Two-tier acquire: process-local threading.Lock first (serializes threads
    # in this process), then file-based O_EXCL lock (serializes across processes).
    if not local.acquire(timeout=max_wait_seconds):
        raise RuntimeError(f"lock busy: {lock_path.name} (local thread timeout)")
    handle = None
    try:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        deadline = time.monotonic() + max_wait_seconds
        backoff_ms = 50
        while True:
            try:
                handle = os.open(str(lock_path), flags)
                break
            except FileExistsError as exc:
                if clear_stale_lock(lock_path, policy=policy):
                    # Stale lock cleared — retry immediately.
                    continue
                # Live holder (different process) — wait with backoff.
                if time.monotonic() >= deadline:
                    raise RuntimeError(
                        f"lock busy: {lock_path.name} (timed out after {max_wait_seconds}s)"
                    ) from exc
                time.sleep(backoff_ms / 1000.0)
                backoff_ms = min(int(backoff_ms * 2), 1000)
        if handle is None:
            raise RuntimeError(f"lock busy: {lock_path.name}")
    except BaseException:
        local.release()
        raise
    try:
        payload = {"pid": os.getpid(), "timestamp": int(time.time())}
        if metadata:
            payload.update(metadata)
        payload_json = json.dumps(payload, indent=2)
        os.write(handle, payload_json.encode("utf-8"))
        yield
    finally:
        if handle is not None:
            os.close(handle)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            # Windows can briefly hold the file (antivirus / file indexer / lazy
            # handle cleanup) and raise WinError 32 here. Leave the orphaned
            # lock to be reaped by clear_stale_lock on the next acquire — the
            # holder's pid is recorded so liveness check will correctly clear it.
            pass
        local.release()


@contextmanager
def lock_group(paths: Sequence[str | Path], *, root: Path | None = None, policy: dict | None = None) -> Iterator[None]:
    """Acquire a group of file locks atomically.

    AC-8: single-path invocation works identically to file_lock.
    Multi-path semantics are reserved for ADR-003 D3 reverse-transition needs.
    """
    if len(paths) == 0:
        yield
        return
    if len(paths) > 1:
        raise NotImplementedError(
            "multi-path lock_group reserved for ADR-003 D3 reverse-transition (lock-ordering not yet specified)"
        )
    base = (root or Path(".")).resolve()
    target = (base / paths[0]).resolve() if not isinstance(paths[0], Path) or not paths[0].is_absolute() else Path(paths[0]).resolve()
    lock_path = lock_path_for_target(base, target)
    with file_lock(lock_path, policy=policy):
        yield


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def append_write(path: Path, content: str, *, policy: dict | None = None) -> None:
    """Append `content` to `path` using O_APPEND, serialized via per-target sidecar lock.

    AC-3, AC-4: caller MUST pass exactly one logical line (typically ending '\\n').
    POSIX provides atomic O_APPEND for writes <= PIPE_BUF, but Windows/Git Bash
    can lose writes under concurrent FDs. Per Lock Designer roundtable Q2 we
    serialize via a per-target sidecar lock for cross-platform portability.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    sidecar = path.with_suffix(path.suffix + ".guard.lock")
    with file_lock(sidecar, policy=policy, max_wait_seconds=30.0):
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        fd = os.open(str(path), flags, 0o644)
        try:
            data = content.encode("utf-8") if isinstance(content, str) else content
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)


def per_target_receipt_path(root: Path, target: Path, receipt_dir: str) -> Path:
    """AC-5: deterministic per-target receipt filename via sha256(rel_posix)[:16]."""
    rel = relative_posix(target, root)
    digest = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16]
    return (root / receipt_dir / f"{digest}.json").resolve()


def write_receipt(
    root: Path,
    receipt_arg: str,
    *,
    target: Path,
    expected_sha: str,
    new_sha: str,
    mode: str = "replace",
    policy: dict | None = None,
) -> Path:
    """Write the per-target receipt; optionally also mirror to the legacy path.

    Returns the per-target receipt path (the new canonical location).
    """
    payload = {
        "target": relative_posix(target, root),
        "timestamp": int(time.time()),
        "expected_sha": expected_sha,
        "new_sha": new_sha,
        "mode": mode,
    }
    payload_json = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    # Per-target receipt (AC-5 — new canonical location)
    if policy is not None and policy.get("per_target_receipts", True):
        receipt = per_target_receipt_path(root, target, policy["receipt_dir"])
    else:
        receipt = (root / receipt_arg).resolve()
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(payload_json, encoding="utf-8")

    # Legacy mirror (AC-22 — Phase 1 dual-write)
    if policy is not None and policy.get("legacy_receipt_mirror", True):
        legacy = (root / receipt_arg).resolve()
        if legacy != receipt:  # avoid double-write when receipt_arg already targets per-target dir
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text(payload_json, encoding="utf-8")

    return receipt


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def cmd_snapshot(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    policy = load_guard_policy(root)
    target = resolve_target(root, args.path, policy=policy, allow_outside=False)
    text, sha = read_text_and_sha(target)
    payload = {
        "path": relative_posix(target, root),
        "exists": text is not None,
        "sha256": sha,
        "size_bytes": len(text.encode("utf-8")) if text is not None else 0,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    policy = load_guard_policy(root)

    try:
        target = resolve_target(root, args.path, policy=policy, allow_outside=args.allow_outside)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    # AC-3: append mode rejects --expected-sha (catches programmer error)
    if args.mode == "append" and args.expected_sha is not None:
        print(
            "append mode is incompatible with --expected-sha "
            "(append is by definition non-atomic against prior content)",
            file=sys.stderr,
        )
        return 1
    if args.mode == "replace" and args.expected_sha is None:
        print("replace mode requires --expected-sha (use 'MISSING' for new files)", file=sys.stderr)
        return 1

    input_path = (root / args.input).resolve()
    if not input_path.is_file():
        print(f"input file not found: {input_path}", file=sys.stderr)
        return 1
    try:
        content = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"could not read input file: {input_path} ({exc})", file=sys.stderr)
        return 1

    lock_path = lock_path_for_target(root, target)

    try:
        with file_lock(
            lock_path,
            metadata={
                "target": relative_posix(target, root),
                "scope": args.lock_key,
                "mode": args.mode,
            },
            policy=policy,
        ):
            if args.mode == "replace":
                _, current_sha = read_text_and_sha(target)
                if current_sha != args.expected_sha:
                    print(
                        json.dumps(
                            {
                                "status": "conflict",
                                "reason": "stale-sha",
                                "expected_sha": args.expected_sha,
                                "actual_sha": current_sha,
                                "path": relative_posix(target, root),
                            },
                            indent=2,
                            sort_keys=True,
                        ),
                        file=sys.stderr,
                    )
                    return 2

                atomic_write(target, content)
                new_sha = sha256_text(content)
            else:  # append
                append_write(target, content)
                # post-append sha for receipt traceability (file may grow further before validator reads)
                _, new_sha = read_text_and_sha(target)

            receipt = write_receipt(
                root,
                args.receipt,
                target=target,
                expected_sha=args.expected_sha if args.mode == "replace" else MISSING_SHA,
                new_sha=new_sha,
                mode=args.mode,
                policy=policy,
            )
    except RuntimeError as exc:
        print(json.dumps({"status": "conflict", "reason": str(exc)}), file=sys.stderr)
        return 3
    except OSError as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "reason": "write-failed",
                    "detail": str(exc),
                    "path": relative_posix(target, root),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 4
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "path": relative_posix(target, root),
                "new_sha": new_sha,
                "mode": args.mode,
                "receipt": str(receipt.relative_to(root)).replace("\\", "/"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "snapshot":
        return cmd_snapshot(args)
    if args.command == "write":
        return cmd_write(args)
    print(f"unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
